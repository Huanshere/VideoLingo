"""Focused offline checks; never start ML or TTS services."""
import ast
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import types

import pytest
import requests
from huggingface_hub.errors import LocalEntryNotFoundError

ROOT = Path(__file__).resolve().parents[1]


def functions(relative, names, namespace):
    tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
    tree.body = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    exec(compile(tree, relative, 'exec'), namespace)
    return namespace


@pytest.fixture
def parse():
    import math
    return functions('core/utils/task_literals.py', ['_NumpyNumbers', 'parse_task_literal'],
                     {'ast': ast, 'math': math})['parse_task_literal']


@pytest.mark.parametrize('text,expected', [
    ('[[np.float64(0.1), np.float32(-2.5)]]', [[.1, -2.5]]),
    ('[[0.1, 1.5]]', [[.1, 1.5]]), ("['hello', 'np.float64(1)']", ['hello', 'np.float64(1)']),
])
def test_legacy_numbers(parse, text, expected):
    assert parse(text) == expected


@pytest.mark.parametrize('text', ["__import__('os').system('echo bad')", 'np.load(1)',
                                    'np.float64(float(1))', 'np.float64("nan")',
                                    'np.float64(1,2)', 'np.float64(1e999)', 'np.float64(True)'])
def test_arbitrary_expressions_rejected(parse, text):
    with pytest.raises((ValueError, TypeError)):
        parse(text)


def test_old_workbook_readers(tmp_path, parse):
    import pandas as pd
    path = tmp_path / 'legacy.xlsx'
    pd.DataFrame({'number': [1], 'lines': ["['Hello', 'World']"],
                  'new_sub_times': ['[[np.float64(0.1), np.float64(1.5)], [1.5, 2.0]]']}).to_excel(path, index=False)
    ns = functions('core/_11_merge_audio.py', ['load_and_flatten_data', 'get_audio_files'],
                   {'pd': pd, 'parse_task_literal': parse, 'OUTPUT_FILE_TEMPLATE': '{0}.wav'})
    table, lines, times = ns['load_and_flatten_data'](path)
    assert lines == ['Hello', 'World'] and times == [[.1, 1.5], [1.5, 2.0]]
    assert ns['get_audio_files'](table) == ['1_0.wav', '1_1.wav']


def test_sovits_network_failure_is_not_ready(monkeypatch):
    class Session:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, *a, **k): raise requests.Timeout('synthetic timeout')
    monkeypatch.setattr(requests, 'Session', Session)
    ready = functions('core/tts_backend/gpt_sovits_tts.py', ['sovits_ready'], {'requests': requests})['sovits_ready']
    assert ready() is False


@pytest.mark.parametrize('mode', ['global', 'project', 'missing', 'partial', 'direct'])
def test_cache_resolution_offline_first(tmp_path, monkeypatch, mode):
    namespace = functions('core/asr_backend/whisperX_local.py',
                          ['_complete_model_directory', 'resolve_whisper_model'],
                          {'Path': Path, 'rprint': lambda *a: None})
    complete = tmp_path / ('project/large-v3' if mode == 'direct' else 'snapshot')
    complete.mkdir(parents=True)
    for name in ('model.bin', 'config.json', 'tokenizer.json'):
        (complete / name).write_bytes(b'fixture')
    partial = tmp_path / 'partial'
    partial.mkdir()
    calls = []
    def download(name, **kwargs):
        calls.append(kwargs)
        if kwargs.get('local_files_only'):
            if mode == 'missing': raise LocalEntryNotFoundError('missing')
            if kwargs['cache_dir'] is not None:
                if mode == 'global': raise LocalEntryNotFoundError('missing')
                if mode == 'partial': return str(partial)
        return str(complete)
    module = types.ModuleType('faster_whisper.utils')
    module.download_model = download
    monkeypatch.setitem(sys.modules, 'faster_whisper.utils', module)
    result = namespace['resolve_whisper_model']('large-v3', tmp_path / 'project')
    assert Path(result) == complete
    assert sum(not c.get('local_files_only', False) for c in calls) == (mode == 'missing')
    if mode == 'direct': assert not calls


@pytest.mark.parametrize('status,schema,expected', [
    (200, {'paths': {'/tts': {'post': {}}, '/set_gpt_weights': {'get': {}}, '/set_sovits_weights': {'get': {}}}}, True),
    (404, {}, False), (400, {}, False), (500, {}, False), (200, {}, False), (200, [], False),
])
def test_sovits_api_identity(monkeypatch, status, schema, expected):
    class Response:
        status_code = status
        def json(self): return schema
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Session:
        trust_env = True
        def get(self, url, **kwargs):
            assert not self.trust_env
            assert url.endswith('/openapi.json') and kwargs == {'timeout': 2, 'allow_redirects': False}
            return Response()
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(requests, 'Session', Session)
    ready = functions('core/tts_backend/gpt_sovits_tts.py', ['sovits_ready'], {'requests': requests})['sovits_ready']
    assert ready() is expected


def test_sovits_exited_child_and_cwd(tmp_path, monkeypatch):
    import socket
    import time
    class Socket:
        def settimeout(self, value): assert value == 2
        def connect_ex(self, address): return 1
        def close(self): pass
    class Child:
        returncode = 7
        def poll(self): return 7
    monkeypatch.setattr(socket, 'socket', lambda *a: Socket())
    def popen(command, **kwargs):
        assert kwargs['cwd'] == tmp_path
        assert command[0] == str(tmp_path / 'runtime' / 'python.exe')
        return Child()
    monkeypatch.setattr(subprocess, 'Popen', popen)
    monkeypatch.setattr(subprocess, 'CREATE_NEW_CONSOLE', 16, raising=False)
    platform = types.SimpleNamespace(platform='win32')
    ns = functions('core/tts_backend/gpt_sovits_tts.py', ['start_gpt_sovits_server'], {
        'Path': Path, '__file__': str(ROOT / 'core/tts_backend/gpt_sovits_tts.py'),
        'socket': socket, 'time': time, 'sys': platform, 'subprocess': subprocess,
        'rprint': lambda *a: None, 'load_key': lambda _: 'voice', 'check_cancel': lambda: None,
        'find_and_check_config_path': lambda _: (tmp_path, tmp_path / 'voice.yaml'),
        'sovits_ready': lambda: pytest.fail('Exited child must not be probed'),
    })
    cwd = Path.cwd()
    with pytest.raises(RuntimeError, match='code 7'):
        ns['start_gpt_sovits_server']()
    assert Path.cwd() == cwd


def test_windows_log_roundtrip(tmp_path):
    powershell = shutil.which('powershell.exe')
    if not powershell: pytest.skip('Windows PowerShell verification')
    path = tmp_path / "log with ' quote.log"
    env = {**os.environ, 'LOGFILE': str(path)}
    # Execute the actual header command and logger, not Streamlit or the launcher.
    batch = (ROOT / 'OneKeyStart.bat').read_text(encoding='utf-8')
    header = next(line for line in batch.splitlines() if line.startswith('powershell -NoProfile -Command "[IO.File]'))
    command = header.split('-Command "', 1)[1][:-1]
    subprocess.run([powershell, '-NoProfile', '-Command', command], env=env, check=True, capture_output=True)
    text = '中文与 café\nsecond line\n'
    result = subprocess.run([powershell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                             str(ROOT / 'scripts/streamlit-log.ps1')],
                            input=text.encode('utf-8'), capture_output=True, check=True, env=env)
    raw = path.read_bytes()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\x00' not in raw
    assert raw.decode('utf-8').splitlines()[1:] == text.splitlines()
    assert result.stdout.decode('utf-8').splitlines() == text.splitlines()
