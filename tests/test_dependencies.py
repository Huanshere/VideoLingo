"""Regression checks for staged installation and shared audio decoding."""
import importlib.util
import io
from pathlib import Path
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
