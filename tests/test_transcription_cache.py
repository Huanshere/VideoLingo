import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from core import _2_asr as asr
from core.asr_backend import transcription_cache as cache, elevenlabs_asr as backend


def result(start=0):
    return {"language": "en", "segments": [{"start": start, "end": start + 1,
            "text": "Example", "words": [{"word": "Example", "start": start, "end": start + 1}]}]}


class TranscriptionCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(os.chdir, self.cwd)
        self.media = Path("input.wav")
        self.media.write_bytes(b"synthetic input one")
        self.whisper = {"runtime": "elevenlabs", "model": "large-v3", "language": "auto"}

    def test_identity_uses_content_and_settings_not_path_or_key(self):
        key = cache.cache_key(self.media, self.whisper, False)
        renamed = Path("renamed.wav")
        renamed.write_bytes(self.media.read_bytes())
        self.assertEqual(key, cache.cache_key(renamed, dict(self.whisper, elevenlabs_api_key="secret"), False))
        for change in ({"language": "ja"}, {"runtime": "local"}, {"model": "tiny"}):
            self.assertNotEqual(key, cache.cache_key(self.media, dict(self.whisper, **change), False))
        self.assertNotEqual(key, cache.cache_key(self.media, self.whisper, True))
        self.media.write_bytes(b"synthetic input two")
        self.assertNotEqual(key, cache.cache_key(self.media, self.whisper, False))

    def test_corrupt_and_invalid_results_are_misses(self):
        cache.write_result("key", "complete", result(), "en")
        path = cache.CACHE_DIR / "key/complete.json"
        path.write_text("{incomplete", encoding="utf-8")
        self.assertIsNone(cache.read_result("key", "complete"))
        cache.write_result("bad", "complete", {"error": "request failed"}, "en")
        self.assertIsNone(cache.read_result("bad", "complete"))
        invalid = result()
        invalid["segments"][0]["words"] = 42
        self.assertFalse(cache.valid_result(invalid))

    def test_failed_atomic_write_does_not_publish_partial_result(self):
        with patch.object(cache.os, "replace", side_effect=OSError("disk full")):
            cache.write_result("key", "complete", result(), "en")
        self.assertIsNone(cache.read_result("key", "complete"))
        self.assertEqual(list((cache.CACHE_DIR / "key").iterdir()), [])

    def run_transcribe(self, transcriber, segments=((0, 1),)):
        config = {"whisper": copy.deepcopy(self.whisper), "demucs": False,
                  "whisper.runtime": self.whisper["runtime"]}
        with patch.object(asr, "find_media_file", return_value=(str(self.media), "audio")), patch.object(
            asr, "load_key", side_effect=config.__getitem__
        ), patch.object(asr, "update_key") as language, patch.object(asr, "check_cancel"), patch.object(
            asr, "prepare_audio_for_asr"
        ) as prepare, patch.object(asr, "split_audio", return_value=segments), patch.object(
            backend, "transcribe_audio_elevenlabs", transcriber
        ):
            asr.transcribe()
            return language, prepare

    def test_complete_hit_recreates_workbook_without_asr_and_keeps_downstream_audio(self):
        transcriber = Mock(return_value=result())
        self.run_transcribe(transcriber)
        expected = pd.read_excel(asr._2_CLEANED_CHUNKS)
        Path(asr._2_CLEANED_CHUNKS).unlink()
        language, prepare = self.run_transcribe(transcriber)
        self.assertEqual(transcriber.call_count, 1)
        prepare.assert_called_once_with(str(self.media))
        language.assert_called_once_with("whisper.detected_language", "en")
        pd.testing.assert_frame_equal(expected, pd.read_excel(asr._2_CLEANED_CHUNKS))

    def test_partial_failure_reuses_successful_segment(self):
        transcriber = Mock(side_effect=[result(), RuntimeError("interrupted")])
        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            self.run_transcribe(transcriber, ((0, 1), (1, 2)))
        self.assertFalse(Path(asr._2_CLEANED_CHUNKS).exists())
        resumed = Mock(return_value=result(1))
        self.run_transcribe(resumed, ((0, 1), (1, 2)))
        resumed.assert_called_once_with(asr._RAW_AUDIO_FILE, asr._RAW_AUDIO_FILE, 1, 2)
        self.assertEqual(len(pd.read_excel(asr._2_CLEANED_CHUNKS)), 2)

    def test_disabled_cache_calls_backend_again(self):
        self.whisper["cache"] = False
        transcriber = Mock(return_value=result())
        self.run_transcribe(transcriber)
        Path(asr._2_CLEANED_CHUNKS).unlink()
        self.run_transcribe(transcriber)
        self.assertEqual(transcriber.call_count, 2)
        self.assertFalse(cache.CACHE_DIR.exists())

    def test_cancelled_result_is_not_cached(self):
        class Cancelled(BaseException):
            pass
        transcriber = Mock(side_effect=Cancelled())
        with self.assertRaises(Cancelled):
            self.run_transcribe(transcriber)
        self.assertFalse(cache.CACHE_DIR.exists())


if __name__ == "__main__":
    unittest.main()
