"""Managed media tools: offline startup, setup failures, and real PATH isolation."""
import os
from pathlib import Path
import subprocess
import sys

import pytest

import runtime_libraries as runtime


@pytest.fixture(autouse=True)
def restore_pydub_converter(monkeypatch):
    from pydub import AudioSegment
    monkeypatch.setattr(AudioSegment, 'converter', AudioSegment.converter)


def fake_tools(directory):
    directory.mkdir()
    suffix = '.exe' if sys.platform == 'win32' else ''
    for name in ('ffmpeg', 'ffprobe'):
        (directory / (name + suffix)).touch()
    return directory


def test_whisperx_audio_probe_without_torchcodec():
    """Optional backend must work with its native file decoder unavailable."""
    import importlib.util
    if importlib.util.find_spec('whisperx') is None:
        pytest.skip('WhisperX is an optional manual install')
    code = r'''
import importlib.abc
import importlib.util
import os
import sys
class NoTorchCodec(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'torchcodec' or fullname.startswith('torchcodec.'):
            return importlib.util.spec_from_loader(fullname, self, is_package=True)
    def create_module(self, spec):
        return None
    def exec_module(self, module):
        raise RuntimeError('TorchCodec shared decoder deliberately unavailable in this test')
sys.meta_path.insert(0, NoTorchCodec())
os.environ['PATH'] = ''
os.environ.pop('VIDEOLINGO_FFMPEG_DLL_DIR', None)
from runtime_libraries import check_whisperx_runtime
check_whisperx_runtime()
'''
    result = subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr


def test_override_is_process_local_and_idempotent(tmp_path, monkeypatch):
    directory = fake_tools(tmp_path / 'media tools')
    monkeypatch.setenv('VIDEOLINGO_FFMPEG_DIR', str(directory))
    monkeypatch.setenv('PATH', 'old-system-tools')
    runtime.configure_ffmpeg(required=True)
    runtime.configure_ffmpeg(required=True)
    assert os.environ['PATH'].split(os.pathsep) == [str(directory), 'old-system-tools']


def test_incomplete_override_is_not_silently_replaced(tmp_path, monkeypatch):
    monkeypatch.setenv('VIDEOLINGO_FFMPEG_DIR', str(tmp_path))
    with pytest.raises(RuntimeError, match='automatically'):
        runtime.configure_ffmpeg()


def test_offline_check_never_downloads(tmp_path, monkeypatch):
    from static_ffmpeg import run
    monkeypatch.delenv('VIDEOLINGO_FFMPEG_DIR', raising=False)
    monkeypatch.setattr(run, 'get_platform_dir', lambda: str(tmp_path))
    monkeypatch.setattr(run, 'get_or_fetch_platform_executables_else_raise',
                        lambda: pytest.fail('An import or health check must not download'))
    assert runtime.configure_ffmpeg() is None
    with pytest.raises(RuntimeError, match='installer.py'):
        runtime.configure_ffmpeg(required=True)


def test_setup_repairs_incomplete_download(tmp_path, monkeypatch):
    from static_ffmpeg import run
    directory = tmp_path / 'managed'
    directory.mkdir()
    marker = directory / 'installed.crumb'
    marker.touch()
    suffix = '.exe' if sys.platform == 'win32' else ''
    surviving_tool = directory / ('ffmpeg' + suffix)
    surviving_tool.touch()
    surviving_tool.chmod(0o555)
    monkeypatch.delenv('VIDEOLINGO_FFMPEG_DIR', raising=False)
    monkeypatch.setattr(run, 'get_platform_dir', lambda: str(directory))
    calls = []
    def fetch():
        assert not marker.exists()
        assert not surviving_tool.exists()
        for name in ('ffmpeg', 'ffprobe'):
            (directory / (name + suffix)).touch()
        calls.append(True)
    monkeypatch.setattr(run, 'get_or_fetch_platform_executables_else_raise', fetch)
    monkeypatch.setenv('PATH', '')
    assert runtime.configure_ffmpeg(download=True, required=True) == directory
    assert calls == [True]


def test_real_tools_work_without_system_ffmpeg(tmp_path):
    """Fresh child process, no system PATH, no network, real pydub/ffprobe/encoding."""
    code = r'''
import os, shutil, socket, subprocess, json
from pathlib import Path
assert shutil.which('ffmpeg') is None
assert shutil.which('ffprobe') is None
def offline(*a, **k):
    raise AssertionError('Runtime tried to access the network')
socket.socket.connect = offline
from runtime_libraries import configure_ffmpeg, validate_ffmpeg
directory = configure_ffmpeg(required=True)
print(validate_ffmpeg())
assert Path(shutil.which('ffmpeg')).parent == directory
assert Path(shutil.which('ffprobe')).parent == directory
from pydub import AudioSegment
from pydub.generators import Sine
from pydub.utils import mediainfo
Sine(440).to_audio_segment(duration=1000).export('test.mp3', format='mp3')
assert abs(len(AudioSegment.from_mp3('test.mp3')) - 1000) < 30
assert 0.95 < float(mediainfo('test.mp3')['duration']) < 1.15
subprocess.run(['ffmpeg', '-v', 'error', '-i', 'test.mp3', '-af', 'atempo=1.25', 'fast.wav'], check=True)
assert 700 < len(AudioSegment.from_wav('fast.wav')) < 850
# Exercise the real decoder without importing the entire UI/model graph in this
# intentionally empty working directory (it expects config.yaml in the cwd).
import ast, numpy as np
source = Path(os.environ['PYTHONPATH']) / 'core/asr_backend/qwen_asr_local.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'load_audio_segment']
namespace = {'subprocess': subprocess, 'np': np, 'SAMPLE_RATE': 16000}
exec(compile(tree, str(source), 'exec'), namespace)
clip = namespace['load_audio_segment']('test.mp3', 0, 0.5)
assert clip.shape == (8000,)
from yt_dlp import YoutubeDL
from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor
with YoutubeDL({'quiet': True}) as ydl:
    postprocessor = FFmpegPostProcessor(ydl)
    assert postprocessor.available
    assert postprocessor.probe_available
    assert Path(shutil.which(postprocessor.executable)).resolve().parent == directory.resolve()
print(json.dumps({'ffmpeg': shutil.which('ffmpeg'), 'ffprobe': shutil.which('ffprobe')}))
'''
    env = {**os.environ, 'PATH': '', 'PYTHONPATH': str(Path(__file__).resolve().parents[1])}
    env.pop('VIDEOLINGO_FFMPEG_DIR', None)
    env.pop('VIDEOLINGO_FFMPEG_DLL_DIR', None)
    result = subprocess.run([sys.executable, '-c', code], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


def test_validation_rejects_build_without_subtitle_filter(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, 'configure_ffmpeg', lambda **kw: tmp_path)
    def run(cmd, **kwargs):
        output = 'ffmpeg version test' if cmd[-1] == '-version' else '... atempo A->A'
        return subprocess.CompletedProcess(cmd, 0, stdout=output)
    monkeypatch.setattr(runtime.subprocess, 'run', run)
    with pytest.raises(RuntimeError, match='subtitles'):
        runtime.validate_ffmpeg()


def test_managed_cli_does_not_hide_whisperx_dlls(tmp_path, monkeypatch):
    if os.name != 'nt':
        pytest.skip('Windows DLL search only')
    managed = fake_tools(tmp_path / 'managed')
    shared = tmp_path / 'shared'
    shared.mkdir()
    (shared / 'avcodec-61.dll').touch()
    monkeypatch.setenv('PATH', os.pathsep.join([str(managed), str(shared)]))
    monkeypatch.delenv('VIDEOLINGO_FFMPEG_DLL_DIR', raising=False)
    monkeypatch.setattr(runtime, '_dll_handles', [])
    calls = []
    monkeypatch.setattr(os, 'add_dll_directory', lambda p: calls.append(p))
    runtime.configure_ffmpeg_dlls()
    assert calls == [str(shared)]
