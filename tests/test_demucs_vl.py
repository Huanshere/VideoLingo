"""Demucs stems must stay sample-aligned with raw.mp3 (no model download: the separator is faked).

Real FFmpeg, the real Demucs reader/writer helpers and the app's own decoders are used, so
the MP3 encoder-delay handling that shifted word timestamps ~60 ms late is exercised.
"""
import subprocess
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("torch")
pytest.importorskip("demucs.api")

from core.asr_backend import demucs_vl
from core.asr_backend.audio_preprocess import normalize_audio_volume
from core.asr_backend.qwen_asr_local import load_audio_segment
from core.utils.models import _BACKGROUND_AUDIO_FILE, _RAW_AUDIO_FILE, _VOCAL_AUDIO_FILE

SR = 16000


def lag(reference, other):
    """Samples by which `other` is late relative to `reference` (FFT cross-correlation)."""
    n = min(len(reference), len(other))
    size = 1 << (2 * n - 1).bit_length()
    corr = np.fft.irfft(np.fft.rfft(other[:n], size) * np.conj(np.fft.rfft(reference[:n], size)), size)
    k = int(np.argmax(corr))
    return k if k < size // 2 else k - size


@pytest.fixture
def raw_mp3(tmp_path, monkeypatch):
    """20 s of noise bursts encoded like raw.mp3 (libmp3lame, 32 kHz mono, 128 kbps)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output/audio").mkdir(parents=True)
    rng = np.random.default_rng(0)
    source = np.zeros(48000 * 20, dtype=np.float32)
    for start in rng.integers(0, len(source) - 4800, 60):
        length = int(rng.integers(800, 4800))
        source[start:start + length] += rng.normal(0, 0.25, length).astype(np.float32)
    source.astype("<f4").tofile("source.f32")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "source.f32",
                    "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "32000", "-ac", "1", _RAW_AUDIO_FILE], check=True)


@pytest.fixture
def fake_demucs(monkeypatch):
    """Identity 'separation' at htdemucs' 44.1 kHz stereo: vocals = 0.8 x, other stems share the rest."""
    calls = {}

    class Separator:
        def __init__(self, model, **kwargs):
            pass

        def separate_tensor(self, wav, sr=None):
            calls["input"] = (tuple(wav.shape), sr)
            return wav, {"vocals": wav * 0.8, "drums": wav * 0.1, "bass": wav * 0.05, "other": wav * 0.05}

    monkeypatch.setattr(demucs_vl, "get_model", lambda name: SimpleNamespace(samplerate=44100, audio_channels=2))
    monkeypatch.setattr(demucs_vl, "PreloadedSeparator", Separator)
    return calls


def test_stems_are_sample_aligned_with_raw(raw_mp3, fake_demucs):
    demucs_vl.demucs_audio()
    channels, samples = fake_demucs["input"][0]
    assert fake_demucs["input"][1] == 44100 and channels == 2
    # FFmpeg decoding trims the encoder delay: 20 s at 44.1 kHz, give or take one MP3 frame.
    assert abs(samples - 20 * 44100) <= 1152

    raw = load_audio_segment(_RAW_AUDIO_FILE, 0, 20)
    for stem in (_VOCAL_AUDIO_FILE, _BACKGROUND_AUDIO_FILE):
        decoded = load_audio_segment(stem, 0, 20)
        # Before the fix: 953 samples (59.6 ms) late. One 16 kHz sample is 0.06 ms.
        assert abs(lag(raw, decoded)) <= 1, stem
        assert abs(len(decoded) - len(raw)) <= SR // 100


def test_vocal_stays_aligned_through_asr_normalization(raw_mp3, fake_demucs):
    # _2_asr re-exports vocal.mp3 through pydub before alignment.
    demucs_vl.demucs_audio()
    normalize_audio_volume(_VOCAL_AUDIO_FILE, _VOCAL_AUDIO_FILE, format="mp3")
    assert abs(lag(load_audio_segment(_RAW_AUDIO_FILE, 0, 20), load_audio_segment(_VOCAL_AUDIO_FILE, 0, 20))) <= 1


def test_reference_clips_read_vocal_without_delay(raw_mp3, fake_demucs):
    # _9_refer_audio slices vocal.mp3 with soundfile by subtitle timestamps.
    sf = pytest.importorskip("soundfile")
    demucs_vl.demucs_audio()
    data, sr = sf.read(_VOCAL_AUDIO_FILE)
    assert sr == 44100
    raw = load_audio_segment(_RAW_AUDIO_FILE, 0, 20)
    vocal = np.interp(np.arange(len(raw)) * sr / SR, np.arange(len(data)), data.mean(axis=1)).astype(np.float32)
    assert abs(lag(raw, vocal)) <= 1


def test_stem_falls_back_to_wav_without_libmp3lame(tmp_path, monkeypatch):
    import torch
    monkeypatch.setattr(demucs_vl, "_ffmpeg_has_encoder", lambda name: False)
    path = tmp_path / "vocal.mp3"
    demucs_vl.save_stem(torch.zeros(2, 4410), path, 44100)
    assert path.read_bytes()[:4] == b"RIFF"
