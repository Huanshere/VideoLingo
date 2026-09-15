"""Regression checks for staged installation and shared audio decoding."""
import ast
import importlib.util
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import wave

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'installer.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


@pytest.mark.parametrize('cuda,tag', [((13, 4),'cu128'), ((12, 8),'cu128'), ((12, 6),'cu126'), (None,'cu126')])
def test_cuda_index(monkeypatch, cuda, tag):
    monkeypatch.setattr(installer, 'detect_cuda_version_from_smi', lambda: cuda)
    assert installer.detect_torch_index().endswith('/' + tag)


@pytest.mark.parametrize('output', ['CUDA Version: 13.3', 'CUDA UMD Version: 13.3'])
def test_driver_cuda_output_formats(monkeypatch, output):
    monkeypatch.setattr(installer.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=output))
    assert installer.detect_cuda_version_from_smi() == (13, 3)


def test_noto_lookup_uses_font_family(monkeypatch):
    monkeypatch.setattr(installer.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(installer.shutil, 'which', lambda _: '/usr/bin/fc-match')
    def match(cmd, **kwargs):
        assert cmd == ['fc-match', 'Noto Sans CJK SC']
        return subprocess.CompletedProcess(cmd, 0, stdout='NotoSansCJK-Regular.ttc: "Noto Sans CJK SC"', stderr='')
    monkeypatch.setattr(installer.subprocess, 'run', match)
    assert installer.noto_cjk_font_available()


def test_requirements_exclude_staged_torch():
    names = {installer.requirement_name(r) for r in installer.read_base_requirements()}
    assert not names.intersection({'torch', 'torchaudio', 'torchvision'})
    assert {'whisperx', 'spacy', 'torchcodec'} <= names
    assert not names.intersection({'moviepy', 'replicate', 'resampy'})


def test_cpu_torch_repaired_on_gpu(monkeypatch):
    versions = {'torch':'2.8.0+cpu', 'torchaudio':'2.8.0+cpu', 'torchvision':'0.23.0+cpu'}
    monkeypatch.setattr(installer, 'package_version', versions.get)
    monkeypatch.setattr(installer, 'detect_nvidia_gpu', lambda: True)
    monkeypatch.setattr(installer, 'detect_torch_index', lambda: installer.TORCH_INDEX + '/cu128')
    calls = []
    monkeypatch.setattr(installer, 'pip_install', lambda packages, **kwargs: calls.append((packages, kwargs)))
    installer.install_torch()
    assert calls and 'torchvision==0.23.0' in calls[0][0]
    assert '--force-reinstall' in calls[0][1]['extra_args']


@pytest.mark.parametrize('backend', ['cu126', 'cu128', 'cpu'])
def test_explicit_backend_without_gpu(monkeypatch, backend):
    monkeypatch.setattr(installer, 'package_version', lambda _: None)
    monkeypatch.setattr(installer, 'detect_nvidia_gpu', lambda: pytest.fail('Explicit build must not probe GPU'))
    monkeypatch.setattr(installer.platform, 'system', lambda: 'Linux')
    calls = []
    monkeypatch.setattr(installer, 'pip_install', lambda packages, **kwargs: calls.append((packages, kwargs)))
    installer.install_torch(backend=backend)
    assert calls[0][0] == ['torch==2.8.0', 'torchaudio==2.8.0', 'torchvision==0.23.0']
    assert installer.TORCH_INDEX + '/' + backend in calls[0][1]['extra_args']


def test_mixed_cuda_builds_are_repaired(monkeypatch):
    versions = {'torch': '2.8.0+cu128', 'torchaudio': '2.8.0+cu126', 'torchvision': '0.23.0+cu128'}
    monkeypatch.setattr(installer, 'package_version', versions.get)
    calls = []
    monkeypatch.setattr(installer, 'pip_install', lambda *args, **kwargs: calls.append(args))
    installer.install_torch(backend='cu128')
    assert len(calls) == 1


def test_plain_macos_cpu_versions_are_reused(monkeypatch):
    versions = {'torch': '2.8.0', 'torchaudio': '2.8.0', 'torchvision': '0.23.0'}
    monkeypatch.setattr(installer, 'package_version', versions.get)
    monkeypatch.setattr(installer, 'pip_install', lambda *args, **kwargs: pytest.fail('Compatible packages should be reused'))
    installer.install_torch(backend='cpu')


def _requirement_versions(builds=('cpu', 'cpu', 'cpu')):
    from packaging.requirements import Requirement
    versions = {}
    for raw in installer.REQUIREMENTS.read_text(encoding='utf-8').splitlines():
        if installer.requirement_name(raw):
            req = Requirement(raw)
            lower = [s.version for s in req.specifier if s.operator in ('==', '>=')]
            versions[req.name] = lower[0] if lower else '1.0'
    for name, version, build in zip(('torch', 'torchaudio', 'torchvision'), ('2.8.0', '2.8.0', '0.23.0'), builds):
        versions[name] = version + ('+' + build if build else '')
    return versions


def _patch_health_environment(monkeypatch, versions, gpu=False):
    monkeypatch.setattr(installer, 'package_version', versions.get)
    monkeypatch.setattr(installer, 'load_state', lambda: {'requirements_hash': installer.requirements_hash()})
    monkeypatch.setattr(installer, 'detect_nvidia_gpu', lambda: gpu)
    monkeypatch.setattr(installer.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(installer.shutil, 'which', lambda _: '/example/ffmpeg')


@pytest.mark.parametrize('builds,backend,expected', [
    (('cu128', 'cu128', 'cu128'), 'cu128', 0),
    (('cu128', 'cu126', 'cu128'), 'auto', 1),
    (('cpu', 'cpu', 'cpu'), 'cu128', 1),
    (('', '', ''), 'cpu', 0),
])
def test_health_checks_build_family(monkeypatch, builds, backend, expected):
    _patch_health_environment(monkeypatch, _requirement_versions(builds), gpu=False)
    assert installer.health_check(quiet=True, check_state=False, torch_backend=backend) == expected


@pytest.mark.parametrize('builds,expected', [
    (('cu128', 'cu128', 'cu128'), 0),
    (('cu126', 'cu126', 'cu126'), 0),
    (('cu118', 'cu118', 'cu118'), 1),
    (('cu129', 'cu129', 'cu129'), 1),
    (('cu126', 'cu128', 'cu126'), 1),
    (('cpu', 'cpu', 'cpu'), 1),
])
def test_health_check_auto_gpu_accepts_only_cu126_cu128(monkeypatch, capsys, builds, expected):
    _patch_health_environment(monkeypatch, _requirement_versions(builds), gpu=True)
    assert installer.health_check(check_state=False, torch_backend='auto') == expected
    output = capsys.readouterr().out
    if not set(builds) <= {'cu126', 'cu128'}:
        assert 'auto accepts only cu126/cu128' in output
        assert f"detected builds: {', '.join(sorted(set(builds)))}" in output


@pytest.mark.parametrize('returncode', [0, 1])
def test_torchcodec_probe_result(monkeypatch, capsys, returncode):
    _patch_health_environment(monkeypatch, _requirement_versions(('', '', '')), gpu=False)
    calls = []
    def probe(cmd, **kwargs):
        calls.append(cmd)
        assert cmd[:2] == [installer.sys.executable, '-c']
        assert 'import torchcodec.decoders' in cmd[2]
        assert kwargs['timeout'] == 60
        return subprocess.CompletedProcess(cmd, returncode, stdout='', stderr='incompatible libavcodec' if returncode else '')
    monkeypatch.setattr(installer.subprocess, 'run', probe)
    assert installer.health_check(check_state=True, torch_backend='cpu') == returncode
    assert len(calls) == 1
    output = capsys.readouterr().out
    if returncode:
        assert 'TorchCodec could not load' in output
        assert 'FFmpeg 7 shared libraries' in output
        assert 'incompatible libavcodec' in output
    else:
        assert 'ERROR:' not in output


@pytest.mark.parametrize('error', [
    OSError('synthetic process launch failure'),
    subprocess.TimeoutExpired('torchcodec probe', 60),
])
def test_torchcodec_probe_exception_is_an_error(monkeypatch, capsys, error):
    _patch_health_environment(monkeypatch, _requirement_versions(), gpu=False)
    def probe(*args, **kwargs):
        raise error
    monkeypatch.setattr(installer.subprocess, 'run', probe)
    assert installer.health_check(check_state=True, torch_backend='cpu') == 1
    output = capsys.readouterr().out
    assert 'TorchCodec runtime check failed' in output
    assert str(error) in output


def _docker_setup_args(dockerfile):
    # Join Docker continuations, then tokenize only RUN instructions. Shell
    # comments and adjacent commands must not supply the missing argument.
    dockerfile = '\n'.join(line for line in dockerfile.splitlines() if not line.lstrip().startswith('#'))
    dockerfile = dockerfile.replace('\\\n', ' ')
    calls = []
    for shell in re.findall(r'^\s*RUN\s+(.+)$', dockerfile, flags=re.MULTILINE | re.IGNORECASE):
        lexer = shlex.shlex(shell, posix=True, punctuation_chars=';&|')
        lexer.whitespace_split = True
        command = []
        for token in [*lexer, ';']:
            if set(token) <= set(';&|'):
                if len(command) >= 2 and Path(command[0]).name in {'python', 'python3'} and command[1] == 'setup_env.py':
                    calls.append(command[2:])
                command = []
            else:
                command.append(token)
    return calls


def _colab_setup_args(notebook):
    calls = []
    for cell in json.loads(notebook)['cells']:
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        # The clone cell uses IPython shell/magic commands.
        source = '\n'.join('pass' if line.lstrip().startswith(('!', '%')) else line for line in source.splitlines())
        for node in ast.walk(ast.parse(source)):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess'
                    and node.func.attr == 'run' and node.args and isinstance(node.args[0], (ast.List, ast.Tuple))):
                continue
            args = node.args[0].elts
            if len(args) >= 2 and isinstance(args[1], ast.Constant) and args[1].value == 'setup_env.py':
                calls.append([arg.value for arg in args[2:] if isinstance(arg, ast.Constant)])
    return calls


@pytest.mark.parametrize('filename,extract', [
    ('Dockerfile', _docker_setup_args),
    ('VideoLingo_colab.ipynb', _colab_setup_args),
])
def test_noninteractive_setup_entry_points_pass_yes(filename, extract):
    calls = extract((ROOT / filename).read_text(encoding='utf-8'))
    assert calls, 'No setup_env.py invocation found'
    assert all('--yes' in args for args in calls)


def test_setup_argument_checks_ignore_decoys():
    dockerfile = '# RUN python3 setup_env.py --yes\nRUN python3 setup_env.py && echo --yes # --yes\n'
    assert _docker_setup_args(dockerfile) == [[]]
    notebook = json.dumps({'cells': [
        {'cell_type': 'markdown', 'source': ["subprocess.run([sys.executable, 'setup_env.py', '--yes'])"]},
        {'cell_type': 'code', 'source': [
            "# subprocess.run([sys.executable, 'setup_env.py', '--yes'])\n",
            "\"subprocess.run([sys.executable, 'setup_env.py', '--yes'])\"\n",
            "subprocess.run([sys.executable, 'setup_env.py'])\n",
        ], 'outputs': [{'text': ["setup_env.py', '--yes'"]}]},
    ]})
    assert _colab_setup_args(notebook) == [[]]


@pytest.mark.parametrize('yes', [True, False])
def test_setup_recreation_confirmation(monkeypatch, tmp_path, yes):
    setup_spec = importlib.util.spec_from_file_location('setup_env', ROOT / 'setup_env.py')
    setup = importlib.util.module_from_spec(setup_spec)
    setup_spec.loader.exec_module(setup)
    args = setup.build_parser().parse_args(['--yes'] if yes else [])
    checks = iter([False, True])
    monkeypatch.setattr(setup, 'python_version_ok', lambda _: next(checks))
    removed, commands, prompts = [], [], []
    monkeypatch.setattr(setup.shutil, 'rmtree', lambda path, **kw: removed.append(path))
    monkeypatch.setattr(setup, 'run', lambda cmd, **kw: commands.append(cmd))
    def answer(prompt):
        assert not yes, '--yes must not prompt'
        prompts.append(prompt)
        return 'n'
    monkeypatch.setattr('builtins.input', answer)
    if yes:
        assert setup.create_venv(tmp_path, yes=args.yes) == setup.venv_python(tmp_path)
        assert removed == [tmp_path]
        assert commands == [['uv', 'venv', '--seed', '--python', setup.PYTHON_VERSION, str(tmp_path)]]
        assert not prompts
    else:
        with pytest.raises(SystemExit, match='Cancelled'):
            setup.create_venv(tmp_path, yes=args.yes)
        assert len(prompts) == 1
        assert not removed and not commands


def test_setup_forwards_backend_without_installing(monkeypatch):
    setup_spec = importlib.util.spec_from_file_location('setup_env', ROOT / 'setup_env.py')
    setup = importlib.util.module_from_spec(setup_spec)
    setup_spec.loader.exec_module(setup)
    calls = []
    monkeypatch.setattr(setup, 'run', lambda cmd, **kwargs: calls.append(cmd))
    args = setup.build_parser().parse_args(['--torch-backend', 'cu126'])
    setup.run_installer(Path('/example/bin/python'), args)
    assert calls[0][calls[0].index('--torch-backend') + 1] == 'cu126'
    assert 'installer.py' == Path(calls[0][1]).name


def test_audio_slice(tmp_path):
    from core.asr_backend.audio_preprocess import audio_slice_wav
    path = tmp_path / 'audio.wav'
    subprocess.run(['ffmpeg', '-v','error','-f','lavfi','-i','sine=frequency=440:duration=3','-ar','44100',str(path)], check=True)
    data = audio_slice_wav(path, 1, 2)
    with wave.open(io.BytesIO(data)) as wav:
        assert wav.getframerate() == 16000
        assert wav.getnchannels() == 1
        samples = wav.readframes(32000)
        assert len(samples) == 32000
    with pytest.raises(ValueError):
        audio_slice_wav(path, 2, 1)


def test_homepage():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(ROOT / 'st.py', default_timeout=60).run()
    assert not app.exception


def test_fractional_tts_durations(monkeypatch):
    import pandas as pd
    from core import _10_gen_audio as audio
    monkeypatch.setattr(audio, 'process_row', lambda row, tasks: (row['number'], 4.08))
    monkeypatch.setattr(audio, 'load_key', lambda key: 'edge_tts' if key == 'tts_method' else 2)
    tasks = pd.DataFrame({'number': range(7)})
    result = audio.generate_tts_audio(tasks)
    assert result['real_dur'].tolist() == [4.08] * 7


def test_edge_tts_uses_current_interpreter(monkeypatch, tmp_path):
    import sys
    from core.tts_backend import edge_tts as backend
    monkeypatch.setattr(backend, 'load_key', lambda key: {'voice':'en-US-JennyNeural'})
    calls = []
    monkeypatch.setattr(backend.subprocess, 'run', lambda cmd, **kwargs: calls.append(cmd))
    backend.edge_tts('hello', tmp_path / 'speech.mp3')
    assert calls[0][:3] == [sys.executable, '-m', 'edge_tts']


def test_numpy_timestamps_roundtrip(monkeypatch, tmp_path):
    import ast
    import numpy as np
    import pandas as pd
    from core import _10_gen_audio as audio
    monkeypatch.setattr(audio, 'load_key', lambda key: 1.2 if key.endswith('accept') else 1.0)
    monkeypatch.setattr(audio, 'adjust_audio_speed', lambda *args: None)
    monkeypatch.setattr(audio, 'get_audio_duration', lambda path: 0.5)
    tasks = pd.DataFrame({'number':[1,2], 'cut_off':[0,1], 'real_dur':[0.5,0.5], 'tol_dur':[1.0,1.0], 'tolerance':[0.0,0.0], 'gap':[np.float64(0.1),0.0], 'start_time':['00:00:00.000','00:00:01.000'], 'end_time':['00:00:01.000','00:00:02.000'], 'lines':[['hello'],['world']]})
    result = audio.merge_chunks(tasks)
    path = tmp_path / 'tasks.xlsx'
    result.to_excel(path, index=False)
    restored = pd.read_excel(path)
    for value in restored['new_sub_times']:
        assert isinstance(ast.literal_eval(value)[0][0], float)


def test_explicit_upgrade_bypasses_healthy_state(monkeypatch):
    monkeypatch.setattr(installer, 'load_state', lambda: {'requirements_hash':'same'})
    monkeypatch.setattr(installer, 'requirements_hash', lambda: 'same')
    monkeypatch.setattr(installer, 'health_check', lambda **kwargs: 0)
    calls = []
    monkeypatch.setattr(installer, 'pip_install', lambda packages, **kwargs: calls.append(kwargs))
    installer.install_base_requirements()
    assert not calls
    installer.install_base_requirements(upgrade=True)
    assert calls[0]['extra_args'] == ['--upgrade']


@pytest.mark.skipif(not __import__('os').environ.get('VIDEOLINGO_TEST_SERVER'), reason='Opt-in live server check')
def test_live_server(tmp_path):
    import socket
    import sys
    import time
    import requests
    from websockets.sync.client import connect
    from streamlit.proto.BackMsg_pb2 import BackMsg
    from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with (tmp_path / 'server.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([sys.executable,'-m','streamlit','run',str(ROOT / 'st.py'),'--server.address=127.0.0.1',f'--server.port={port}','--server.headless=true','--browser.gatherUsageStats=false'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        try:
            session = requests.Session()
            session.trust_env = False
            deadline = time.monotonic() + 45
            while True:
                assert proc.poll() is None
                try:
                    if session.get(f'http://127.0.0.1:{port}/_stcore/health',timeout=2).ok:
                        break
                except requests.RequestException:
                    pass
                assert time.monotonic() < deadline
                time.sleep(0.2)
            with connect(f'ws://127.0.0.1:{port}/_stcore/stream',origin=f'http://127.0.0.1:{port}',subprotocols=['streamlit'],proxy=None,max_size=10_000_000) as ws:
                request = BackMsg()
                request.rerun_script.query_string = ''
                ws.send(request.SerializeToString())
                saw_delta = False
                while True:
                    msg = ForwardMsg.FromString(ws.recv(timeout=60))
                    if msg.WhichOneof('type') == 'delta':
                        saw_delta = True
                        assert not msg.delta.new_element.HasField('exception')
                    if msg.WhichOneof('type') == 'script_finished':
                        assert saw_delta and msg.script_finished == ForwardMsg.FINISHED_SUCCESSFULLY
                        break
        finally:
            proc.terminate()
            proc.wait(timeout=20)
