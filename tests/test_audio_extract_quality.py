"""Offline regressions for raw extraction quality and reference audio (#533); no models, TTS or network."""
import ast
import math
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(relative, names, namespace, keep_assign=False):
    """Exec selected top-level functions (optionally plus module constants) without importing core."""
    tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
    tree.body = [
        node for node in tree.body
        if (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names)
        or (keep_assign and isinstance(node, ast.Assign))
    ]
    exec(compile(tree, relative, 'exec'), namespace)
    return namespace


def extraction(directory, config, encoder=True, real_encoder_probe=False):
    namespace = {
        'os': os, 'subprocess': subprocess, 'rprint': lambda *args: None,
        '_AUDIO_DIR': str(directory), '_RAW_AUDIO_FILE': str(directory / 'raw.mp3'),
        'load_key_or': lambda key, default: config.get(key, default),
    }
    names = {'raw_audio_settings', '_raw_audio_command', 'convert_video_to_audio', 'prepare_audio_for_asr'}
    if real_encoder_probe:
        names.add('_ffmpeg_has_encoder')
    else:
        namespace['_ffmpeg_has_encoder'] = lambda _: encoder
    return load('core/asr_backend/audio_preprocess.py', names, namespace, keep_assign=True)


# ---------------------------------------------------------------------------
# Step 2: raw extraction quality (v2.2.1 parity, configurable)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('encoder', [True, False], ids=['mp3', 'pcm-fallback'])
@pytest.mark.parametrize('config,rate,bitrate', [
    ({}, '32000', '128k'),
    ({'audio.raw_sample_rate': 44100, 'audio.raw_bitrate': '192k'}, '44100', '192k'),
], ids=['old-config-without-keys', 'configured'])
def test_raw_extraction_uses_v2_quality_by_default(tmp_path, monkeypatch, encoder, config, rate, bitrate):
    namespace = extraction(tmp_path, config, encoder)
    commands = []
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: commands.append(command))
    namespace['convert_video_to_audio']('video.mp4')
    namespace['prepare_audio_for_asr']('upload.wav')
    assert len(commands) == 2
    for command in commands:
        assert command[command.index('-ar') + 1] == rate
        assert command[command.index('-af') + 1] == 'aresample=async=1:first_pts=0'
        if encoder:
            assert command[command.index('-b:a') + 1] == bitrate
        else:
            assert '-b:a' not in command and command[command.index('-c:a') + 1] == 'pcm_s16le'


def test_sample_rate_below_recognition_rate_is_rejected(tmp_path):
    namespace = extraction(tmp_path, {'audio.raw_sample_rate': 8000})
    with pytest.raises(ValueError):
        namespace['raw_audio_settings']()


def band_level(pcm_path, low, high):
    import numpy as np
    pcm = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(pcm_path), '-ac', '1', '-ar', '48000', '-f', 'f32le', 'pipe:1',
    ])
    samples = np.frombuffer(pcm, dtype=np.float32)
    n = 8192
    frames = samples[:len(samples) // n * n].reshape(-1, n) * np.hanning(n)
    power = np.mean(np.abs(np.fft.rfft(frames, axis=1)) ** 2, axis=0)
    freqs = np.fft.rfftfreq(n, 1 / 48000)
    return 10 * math.log10(float(np.mean(power[(freqs >= low) & (freqs < high)])) + 1e-20)


def test_extracted_audio_keeps_high_band(tmp_path):
    """White noise keeps its 9-14 kHz energy under the default settings; the 3.0.0 16 kHz path lost it."""
    if not shutil.which('ffmpeg'):
        pytest.skip('Real extraction test requires FFmpeg')
    pytest.importorskip('numpy')
    source = tmp_path / 'noise.wav'
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
        'anoisesrc=color=white:sample_rate=48000:duration=3:amplitude=0.3:seed=7',
        '-c:a', 'pcm_s16le', str(source),
    ], check=True, capture_output=True)
    namespace = extraction(tmp_path, {}, real_encoder_probe=True)
    namespace['convert_video_to_audio'](str(source))
    restored = tmp_path / 'raw.mp3'
    legacy = tmp_path / 'legacy.mp3'
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-i', str(source), '-c:a', 'pcm_s16le', '-ar', '16000', '-ac', '1',
        '-f', 'wav', str(legacy),
    ], check=True, capture_output=True)
    for path, expected_drop in ((restored, 6.0), (legacy, 40.0)):
        drop = band_level(path, 1000, 3000) - band_level(path, 9000, 14000)
        if expected_drop < 10:
            assert drop < expected_drop, f'{path.name} lost its high band ({drop:.1f} dB)'
        else:
            assert drop > expected_drop, f'{path.name} unexpectedly kept its high band ({drop:.1f} dB)'


# ---------------------------------------------------------------------------
# Normalization: gain must never push peaks into clipping
# ---------------------------------------------------------------------------

def normalizer():
    from pydub import AudioSegment
    return load('core/asr_backend/audio_preprocess.py', {'normalize_audio_volume'},
                {'AudioSegment': AudioSegment, 'rprint': lambda *args: None, 'math': math})['normalize_audio_volume']


def test_normalize_limits_gain_to_peak_headroom(tmp_path):
    from pydub import AudioSegment
    from pydub.generators import Sine
    burst = Sine(440, sample_rate=16000).to_audio_segment(duration=60, volume=-1.0)
    sparse = burst + AudioSegment.silent(duration=10000, frame_rate=16000)
    source = tmp_path / 'sparse.wav'
    sparse.export(source, format='wav')
    assert -20.0 - sparse.dBFS > -1.0 - sparse.max_dBFS, 'fixture must want more gain than the peak allows'
    output = normalizer()(str(source), str(tmp_path / 'normalized.wav'))
    result = AudioSegment.from_wav(output)
    assert -1.3 <= result.max_dBFS <= -0.9


def test_normalize_still_attenuates_loud_input(tmp_path):
    from pydub import AudioSegment
    from pydub.generators import Sine
    loud = Sine(440, sample_rate=16000).to_audio_segment(duration=1000, volume=-1.0)
    source = tmp_path / 'loud.wav'
    loud.export(source, format='wav')
    result = AudioSegment.from_wav(normalizer()(str(source), str(tmp_path / 'normalized.wav')))
    assert abs(result.dBFS - (-20.0)) < 0.2


def test_normalize_survives_silence(tmp_path):
    from pydub import AudioSegment
    source = tmp_path / 'silence.wav'
    AudioSegment.silent(duration=500, frame_rate=16000).export(source, format='wav')
    output = normalizer()(str(source), str(tmp_path / 'normalized.wav'))
    assert Path(output).stat().st_size > 0


# ---------------------------------------------------------------------------
# SiliconFlow Fish custom voice: merged reference keeps 44.1 kHz
# ---------------------------------------------------------------------------

def test_custom_voice_reference_is_merged_at_44k(tmp_path):
    from pydub import AudioSegment
    from pydub.generators import Sine
    namespace = load('core/tts_backend/sf_fishtts.py', {'merge_audio'}, {
        'AudioSegment': AudioSegment, 'os': os, 'rprint': lambda *args: None,
        'except_handler': lambda *args, **kwargs: (lambda func: func),
    }, keep_assign=True)
    clips = []
    for index in (1, 2):
        clip = tmp_path / f'{index}.wav'
        Sine(300 * index, sample_rate=44100).to_audio_segment(duration=300).export(clip, format='wav')
        clips.append(str(clip))
    output = tmp_path / 'combined_reference.wav'
    assert namespace['merge_audio'](clips, str(output)) is True
    merged = AudioSegment.from_wav(output)
    assert merged.frame_rate == 44100 and merged.channels == 1
    assert abs(len(merged) - (300 + 100) * 2) <= 5


# ---------------------------------------------------------------------------
# Config: optional keys and shipped defaults
# ---------------------------------------------------------------------------

def test_optional_config_key_falls_back_without_error():
    def load_key(key):
        if key == 'present':
            return 'value'
        raise KeyError(key)
    namespace = load('core/utils/config_utils.py', {'load_key_or'}, {'load_key': load_key})
    assert namespace['load_key_or']('present', 'default') == 'value'
    assert namespace['load_key_or']('missing.key', 'default') == 'default'


def test_shipped_config_restores_v2_extraction_defaults():
    yaml = pytest.importorskip('yaml')
    config = yaml.safe_load((ROOT / 'config.yaml').read_text(encoding='utf-8'))
    assert config['audio'] == {'raw_sample_rate': 32000, 'raw_bitrate': '128k'}
