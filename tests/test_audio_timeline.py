"""Local synthetic media regressions; no downloads, models, or API requests."""
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def extraction_functions(directory, encoder):
    # Exercise the real extraction functions without importing ASR/ML dependencies.
    tree = ast.parse((ROOT / 'core/asr_backend/audio_preprocess.py').read_text(encoding='utf-8'))
    names = {'convert_video_to_audio', 'prepare_audio_for_asr', '_raw_audio_command', 'raw_audio_settings'}
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {
        'os': os, 'subprocess': subprocess, 'rprint': lambda *args: None,
        '_AUDIO_DIR': str(directory), '_RAW_AUDIO_FILE': str(directory / 'raw.mp3'),
        '_ffmpeg_has_encoder': lambda _: encoder,
        'load_key_or': lambda key, default: default,
        'RAW_AUDIO_SAMPLE_RATE': 32000, 'RAW_AUDIO_BITRATE': '128k',
    }
    exec(compile(tree, 'audio_preprocess.py', 'exec'), namespace)
    return namespace


@pytest.mark.parametrize('function', ['convert_video_to_audio', 'prepare_audio_for_asr'])
@pytest.mark.parametrize('encoder', [True, False])
def test_all_extraction_paths_preserve_timeline(tmp_path, monkeypatch, function, encoder):
    namespace = extraction_functions(tmp_path, encoder)
    commands = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: commands.append(command))
    namespace[function]('synthetic.nut')
    command = commands[0]
    assert command[command.index('-af') + 1] == 'aresample=async=1:first_pts=0'
    assert command[command.index('-c:a') + 1] == ('libmp3lame' if encoder else 'pcm_s16le')


def test_existing_audio_is_not_overwritten(tmp_path, monkeypatch):
    namespace = extraction_functions(tmp_path, False)
    raw = tmp_path / 'raw.mp3'
    raw.write_bytes(b'existing audio')
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('Existing audio must be retained'))
    namespace['convert_video_to_audio']('synthetic.nut')
    assert raw.read_bytes() == b'existing audio'


@pytest.mark.parametrize('shift', [0, -0.2, 0.2], ids=['continuous', 'overlaps', 'gaps'])
def test_decoded_duration_follows_source_clock(tmp_path, shift):
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        pytest.skip('Synthetic timeline test requires FFmpeg and ffprobe')
    source = tmp_path / 'source.nut'
    subprocess.run([
        ffmpeg, '-v', 'error', '-f', 'lavfi', '-i',
        'sine=frequency=440:sample_rate=44100:duration=12',
        '-af', f'asetpts=PTS+floor(T/2)*({shift})/TB',
        '-c:a', 'pcm_s16le', str(source),
    ], check=True, capture_output=True)
    frames = json.loads(subprocess.check_output([
        ffprobe, '-v', 'error', '-select_streams', 'a:0', '-show_frames',
        '-show_entries', 'frame=pts_time,nb_samples', '-of', 'json', str(source),
    ]))['frames']
    end = float(frames[-1]['pts_time']) + int(frames[-1]['nb_samples']) / 44100
    start = float(frames[0]['pts_time'])
    expected = end - start

    namespace = extraction_functions(tmp_path, False)
    namespace['convert_video_to_audio'](str(source))

    def decoded_duration(path):
        pcm = subprocess.check_output([
            ffmpeg, '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '16000',
            '-f', 's16le', 'pipe:1',
        ])
        return len(pcm) / (16000 * 2)

    corrected = decoded_duration(tmp_path / 'raw.mp3')
    legacy = decoded_duration(source)
    assert abs(corrected - expected) < 0.12
    if shift:
        assert abs(legacy - expected) > 0.8
    else:
        assert abs(corrected - legacy) < 0.005
