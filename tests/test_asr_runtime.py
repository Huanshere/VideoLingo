import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core import _2_asr as asr
from core.asr_backend import qwen_asr_local


def result():
    return {"language": "en", "segments": [{"start": 0, "end": 1, "text": "Example",
            "words": [{"word": "Example", "start": 0, "end": 1}]}]}


class RetiredRuntimeTests(unittest.TestCase):
    def test_retired_runtime_fails_before_preparing_audio(self):
        with patch.object(asr, "load_key", return_value="cloud"), patch.object(
            asr, "find_media_file"
        ) as find:
            with self.assertRaisesRegex(ValueError, "retired"):
                asr.transcribe.__wrapped__()
            find.assert_not_called()

    def test_supported_runtimes_reach_media_discovery(self):
        for runtime in ("local", "elevenlabs"):
            with self.subTest(runtime=runtime), patch.object(asr, "load_key", return_value=runtime), patch.object(
                asr, "find_media_file", side_effect=FileNotFoundError("synthetic missing input")
            ):
                with self.assertRaisesRegex(FileNotFoundError, "synthetic missing input"):
                    asr.transcribe.__wrapped__()



class LocalBackendTests(unittest.TestCase):
    def test_backend_defaults_to_qwen_and_rejects_unknown(self):
        self.assertEqual(asr.local_backend({}), "qwen")
        self.assertEqual(asr.local_backend({"backend": "WhisperX"}), "whisperx")
        with self.assertRaisesRegex(ValueError, "whisper.backend"):
            asr.local_backend({"backend": "funasr"})

    def run_local(self, whisper):
        """Run transcribe() for runtime=local with fake Qwen and WhisperX backends; return what ran."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        cwd = os.getcwd()
        os.chdir(temp.name)
        self.addCleanup(os.chdir, cwd)
        Path("input.wav").write_bytes(b"synthetic input")
        whisper = dict({"runtime": "local", "model": "large-v3", "language": "en"}, **whisper)
        config = {"whisper": whisper, "demucs": False, "whisper.runtime": "local"}
        qwen = Mock(return_value=result())
        whisperx = Mock(return_value=result())
        fake_whisperx = types.ModuleType("core.asr_backend.whisperX_local")
        fake_whisperx.transcribe_audio = whisperx
        key = Mock(return_value=None)
        with patch.object(asr, "find_media_file", return_value=("input.wav", "audio")), patch.object(
            asr, "load_key", side_effect=config.__getitem__
        ), patch.object(asr, "update_key"), patch.object(asr, "check_cancel"), patch.object(
            asr, "prepare_audio_for_asr"
        ), patch.object(asr, "split_audio", return_value=((0, 1),)), patch.object(
            asr.cache, "cache_key", key
        ), patch.object(qwen_asr_local, "transcribe_audio", qwen), patch.object(
            qwen_asr_local, "resolve_engine", return_value="transformers"
        ) as engine, patch.object(qwen_asr_local, "load_key_or", lambda key, default: default), patch.dict(
            sys.modules, {"core.asr_backend.whisperX_local": fake_whisperx}
        ):
            asr.transcribe()
        return qwen, whisperx, key.call_args.args[1], engine

    def test_missing_backend_key_runs_qwen_with_resolved_cache_identity(self):
        qwen, whisperx, identity, engine = self.run_local({"qwen_engine": "auto"})
        qwen.assert_called_once_with(asr._RAW_AUDIO_FILE, asr._RAW_AUDIO_FILE, 0, 1)
        whisperx.assert_not_called()
        engine.assert_called_once_with("auto")
        self.assertEqual((identity["backend"], identity["qwen_model"], identity["qwen_engine"]),
                         ("qwen", "1.7b", "transformers"))

    def test_whisperx_backend_keeps_original_path(self):
        qwen, whisperx, identity, engine = self.run_local({"backend": "whisperx", "qwen_model": "0.6b"})
        whisperx.assert_called_once_with(asr._RAW_AUDIO_FILE, asr._RAW_AUDIO_FILE, 0, 1)
        qwen.assert_not_called()
        engine.assert_not_called()
        self.assertEqual(identity["backend"], "whisperx")


if __name__ == "__main__":
    unittest.main()
