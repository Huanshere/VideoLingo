"""Opt-in real GPU + LLM + TTS integration; never runs without explicit inputs.

Set VIDEOLINGO_TEST_AUDIO, VIDEOLINGO_TEST_API_KEY and optionally
VIDEOLINGO_TEST_BASE_URL / VIDEOLINGO_TEST_MODEL, then run pytest on this file.
The test spends API credits and writes all media into pytest's temporary directory.
"""
import os
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

pytestmark = pytest.mark.skipif(
    not os.environ.get('VIDEOLINGO_TEST_AUDIO') or not os.environ.get('VIDEOLINGO_TEST_API_KEY'),
    reason='Real pipeline requires explicit audio and API credentials',
)


@pytest.fixture
def configured_workdir(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    cfg = yaml.safe_load((root / 'config.yaml').read_text(encoding='utf-8'))
    cfg['api'].update(key=os.environ['VIDEOLINGO_TEST_API_KEY'], base_url=os.environ.get('VIDEOLINGO_TEST_BASE_URL','https://api.openai.com/v1'), model=os.environ.get('VIDEOLINGO_TEST_MODEL','gpt-4o-mini'))
    cfg['whisper'].update(language='en', detected_language='en', runtime='local')
    cfg['tts_method'] = 'edge_tts'
    cfg['demucs'] = True
    cfg['burn_subtitles'] = True
    cfg['pause_before_translate'] = False
    (tmp_path / 'config.yaml').write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding='utf-8')
    shutil.copyfile(root / 'custom_terms.xlsx', tmp_path / 'custom_terms.xlsx')
    monkeypatch.chdir(tmp_path)
    Path('output').mkdir()
    try:
        yield tmp_path
    finally:
        # Do not retain the real API credential in pytest artifacts.
        (tmp_path / 'config.yaml').unlink(missing_ok=True)


def test_video_translation_and_dubbing(configured_workdir):
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=640x360:r=25','-i',os.environ['VIDEOLINGO_TEST_AUDIO'],'-shortest','-c:v','libx264','-c:a','aac','output/sample.mp4'],check=True)
    from core import _2_asr, _3_1_split_nlp, _3_2_split_meaning, _4_1_summarize, _4_2_translate, _5_split_sub, _6_gen_sub, _7_sub_into_vid, _8_1_audio_task, _8_2_dub_chunks, _9_refer_audio, _10_gen_audio, _11_merge_audio, _12_dub_to_vid
    steps = [_2_asr.transcribe, _3_1_split_nlp.split_by_spacy, _3_2_split_meaning.split_sentences_by_meaning, _4_1_summarize.get_summary, _4_2_translate.translate_all, _5_split_sub.split_for_sub_main, _6_gen_sub.align_timestamp_main, _7_sub_into_vid.merge_subtitles_to_video, _8_1_audio_task.gen_audio_task_main, _8_2_dub_chunks.gen_dub_chunks, _9_refer_audio.extract_refer_audio_main, _10_gen_audio.gen_audio, _11_merge_audio.merge_full_audio, _12_dub_to_vid.merge_video_audio]
    from core.st_utils.task_runner import TaskRunner
    runner = TaskRunner()
    runner.start([(func.__name__,func) for func in steps])
    runner._thread.join(timeout=1200)
    assert not runner._thread.is_alive(), 'Pipeline timed out'
    assert runner.state == 'completed', runner.error_msg
    for filename in ('src.srt','trans.srt','output_sub.mp4','output_dub.mp4','dub.mp3'):
        assert (Path('output') / filename).stat().st_size > 0
    translated = Path('output/trans.srt').read_text(encoding='utf-8')
    assert any('\u4e00' <= c <= '\u9fff' for c in translated)


def test_audio_only_translation(configured_workdir):
    shutil.copyfile(os.environ['VIDEOLINGO_TEST_AUDIO'], 'output/sample.wav')
    from core.utils import update_key
    update_key('demucs', False)
    from core import _2_asr, _3_1_split_nlp, _3_2_split_meaning, _4_1_summarize, _4_2_translate, _5_split_sub, _6_gen_sub, _7_sub_into_vid
    steps = [_2_asr.transcribe, _3_1_split_nlp.split_by_spacy, _3_2_split_meaning.split_sentences_by_meaning, _4_1_summarize.get_summary, _4_2_translate.translate_all, _5_split_sub.split_for_sub_main, _6_gen_sub.align_timestamp_main, _7_sub_into_vid.merge_subtitles_to_video]
    for step in steps:
        step()
    assert Path('output/src.srt').stat().st_size > 0
    assert any('\u4e00' <= c <= '\u9fff' for c in Path('output/trans.srt').read_text(encoding='utf-8'))
    assert not Path('output/output_sub.mp4').exists()
