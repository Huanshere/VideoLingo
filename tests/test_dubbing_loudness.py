"""Real FFmpeg checks with synthetic audio; no TTS, network or service startup."""
import ast
import json
import math
from pathlib import Path
import shutil
import subprocess

import pytest
from pydub import AudioSegment
from pydub.generators import Sine


@pytest.fixture
def normalize():
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg is required')
    path = Path(__file__).resolve().parents[1] / 'core/_12_dub_to_vid.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'normalize_dub_audio']
    namespace = dict(subprocess=subprocess, json=json, math=math, check_cancel=lambda: None)
    exec(compile(tree, str(path), 'exec'), namespace)
    return namespace['normalize_dub_audio']


def render(tmp_path, normalize, name, audio):
    source, target = tmp_path / f'{name}.wav', tmp_path / f'{name}-normalized.wav'
    audio.export(source, format='wav')
    normalize(source, target)
    output = AudioSegment.from_wav(target)
    assert output.frame_count() == audio.frame_count()
    assert output.frame_rate == audio.frame_rate
    assert output.channels == audio.channels
    return output


def test_silence_does_not_drive_speech_gain(tmp_path, normalize):
    voice = Sine(440, sample_rate=48000).to_audio_segment(duration=6000).apply_gain(-15)
    silence = AudioSegment.silent(duration=6000, frame_rate=48000)
    continuous = render(tmp_path, normalize, 'continuous', voice)
    padded = render(tmp_path, normalize, 'padded', silence + voice + silence)
    assert abs(continuous[1000:5000].dBFS - padded[7000:11000].dBFS) < 0.3
    assert padded[1000:5000].rms == 0


def test_gain_preserves_sentence_dynamics_and_peak_headroom(tmp_path, normalize):
    tone = Sine(440, sample_rate=48000).to_audio_segment(duration=3000)
    source = tone.apply_gain(-12) + tone.apply_gain(-24)
    output = render(tmp_path, normalize, 'dynamics', source)
    assert abs((output[500:2500].dBFS - output[3500:5500].dBFS) - 12) < 0.1
    assert output.max_dBFS <= -0.99


def test_transient_peak_limits_gain(tmp_path, normalize):
    tone = Sine(440, sample_rate=48000).to_audio_segment(duration=6000).apply_gain(-35)
    transient = Sine(1000, sample_rate=48000).to_audio_segment(duration=10)
    source = tone.overlay(transient, position=3000)
    output = render(tmp_path, normalize, 'transient', source)
    assert output.max_dBFS <= -0.9


def test_silent_audio_remains_silent(tmp_path, normalize):
    output = render(tmp_path, normalize, 'silence', AudioSegment.silent(duration=2000, frame_rate=48000))
    assert output.rms == 0


def test_short_stereo_clip_is_preserved(tmp_path, normalize):
    tone = Sine(440, sample_rate=44100).to_audio_segment(duration=100).apply_gain(-12)
    stereo = AudioSegment.from_mono_audiosegments(tone, tone.apply_gain(-6))
    output = render(tmp_path, normalize, 'short-stereo', stereo)
    assert abs(output.dBFS - stereo.dBFS) < 0.1


def test_ffmpeg_failure_is_reported(tmp_path, normalize):
    with pytest.raises(subprocess.CalledProcessError):
        normalize(tmp_path / 'missing.wav', tmp_path / 'output.wav')


def test_final_video_merge_with_real_ffmpeg(tmp_path, monkeypatch):
    import cv2
    from core import _1_ytdlp, _12_dub_to_vid as merge

    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        pytest.skip('FFmpeg and FFprobe are required')
    # Every generated file stays in the isolated workspace, including relative paths.
    monkeypatch.chdir(tmp_path)
    Path('output').mkdir()
    source = Path('output/source.mp4')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'lavfi',
                    '-i', 'color=c=black:s=320x240:r=25:d=6', '-c:v', 'mpeg4', str(source)], check=True)
    tone = Sine(440, sample_rate=48000).to_audio_segment(duration=6000).apply_gain(-18)
    tone.export('output/dub.mp3', format='mp3', bitrate='64k')
    tone.apply_gain(-12).export('output/background.wav', format='wav')
    Path('output/dub.srt').write_text('1\n00:00:00,000 --> 00:00:06,000\nSynthetic test\n', encoding='utf-8')
    monkeypatch.setattr(_1_ytdlp, 'is_audio_only_input', lambda: False)
    monkeypatch.setattr(merge, 'find_video_files', lambda: str(source))
    monkeypatch.setattr(merge, '_BACKGROUND_AUDIO_FILE', 'output/background.wav')
    monkeypatch.setattr(merge, 'load_key', {'burn_subtitles': True, 'ffmpeg_gpu': False}.__getitem__)
    monkeypatch.setattr(merge, 'check_cancel', lambda: None)
    monkeypatch.setattr(merge, 'TRANS_FONT_NAME', 'Arial')
    merge.merge_video_audio()
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json',
                            'output/output_dub.mp4'], check=True, capture_output=True, text=True)
    streams = json.loads(probe.stdout)['streams']
    audio = next(stream for stream in streams if stream['codec_type'] == 'audio')
    video = next(stream for stream in streams if stream['codec_type'] == 'video')
    assert audio['codec_name'] == 'aac'
    assert abs(float(audio['duration']) - 6.0) < 0.1
    assert abs(float(video['duration']) - 6.0) < 0.1
    assert Path('output/normalized_dub.wav').is_file()
