import importlib.util
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
            def load_key(key, _runtime=runtime):
                if key == "whisper":
                    return {"runtime": _runtime, "language": "en", "model": "large-v3"}
                return _runtime
            with self.subTest(runtime=runtime), patch.object(asr, "load_key", side_effect=load_key), patch.object(
                asr, "find_media_file", side_effect=FileNotFoundError("synthetic missing input")
            ):
                with self.assertRaisesRegex(FileNotFoundError, "synthetic missing input"):
                    asr.transcribe.__wrapped__()

    def test_missing_whisperx_fails_before_preparing_audio(self):
        def load_key(key):
            if key == "whisper.runtime":
                return "local"
            if key == "whisper":
                return {"runtime": "local", "backend": "whisperx", "language": "en", "model": "large-v3"}
            raise AssertionError(key)
        with patch.object(asr, "load_key", side_effect=load_key), patch.object(
            asr, "find_media_file"
        ) as find, patch("importlib.util.find_spec", return_value=None):
            with self.assertRaises(RuntimeError) as caught:
                asr.transcribe.__wrapped__()
        find.assert_not_called()
        message = str(caught.exception)
        self.assertIn("docs/pages/docs/whisperx-manual.en-US.md", message)
        self.assertIn("whisper.backend to qwen", message)
        self.assertNotIn("--local-whisperx", message)
        self.assertNotIn("setup_env", message)
        self.assertNotIn("optional install", message.lower())



class LocalBackendTests(unittest.TestCase):
    def test_backend_defaults_to_qwen_and_rejects_unknown(self):
        self.assertEqual(asr.local_backend({}), "qwen")
        self.assertEqual(asr.local_backend({"backend": "WhisperX"}), "whisperx")
        with self.assertRaisesRegex(ValueError, "whisper.backend"):
            asr.local_backend({"backend": "funasr"})

    def run_local(self, whisper, qwen_result=None, real_qwen=False):
        """Run transcribe() for runtime=local with fake Qwen and WhisperX backends; return what ran."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        cwd = os.getcwd()
        os.chdir(temp.name)
        self.addCleanup(os.chdir, cwd)
        Path("input.wav").write_bytes(b"synthetic input")
        whisper = dict({"runtime": "local", "model": "large-v3", "language": "en"}, **whisper)
        config = {"whisper": whisper, "demucs": False, "whisper.runtime": "local"}
        qwen = Mock(return_value=qwen_result or result())
        whisperx = Mock(return_value=result())
        fake_whisperx = types.ModuleType("core.asr_backend.whisperX_local")
        fake_whisperx.transcribe_audio = whisperx
        key = Mock(return_value=None)
        real_find_spec = importlib.util.find_spec

        def find_spec(name, package=None):
            if name == "whisperx":
                return object()
            return real_find_spec(name, package)

        with patch("importlib.util.find_spec", side_effect=find_spec), patch.object(
            asr, "find_media_file", return_value=("input.wav", "audio")
        ), patch.object(
            asr, "load_key", side_effect=config.__getitem__
        ), patch.object(asr, "update_key"), patch.object(asr, "check_cancel"), patch.object(
            asr, "prepare_audio_for_asr"
        ), patch.object(asr, "split_audio", return_value=((0, 1),)), patch.object(
            asr.cache, "cache_key", key
        ), patch.object(qwen_asr_local, "transcribe_audio", qwen_asr_local.transcribe_audio if real_qwen else qwen), patch.object(
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

    def test_forced_wrong_language_fails_through_the_real_qwen_backend(self):
        # The "still degenerate" branch end to end: real qwen_asr_local.transcribe_audio with only
        # the model session faked, reached from _2_asr.transcribe; nothing is written or cached.
        import contextlib
        import numpy as np
        audio = np.linspace(0, 1, 120 * qwen_asr_local.SAMPLE_RATE, dtype=np.float32)

        @contextlib.contextmanager
        def session(engine, repo_id):
            yield lambda clip, language, max_tokens=None: (("Chinese,English", "我们今天开一个meeting然后presentation要准备好客户那边说要double check一下细节" * 2)
                                          if language is None else (language, "Yeah, yeah, yeah."))
        keys = {"whisper.language": "en", "model_dir": "_model_cache"}
        with patch.object(qwen_asr_local, "asr_session", session), patch.object(
            qwen_asr_local, "load_audio_segment", return_value=audio
        ), patch.object(qwen_asr_local, "load_key", side_effect=keys.__getitem__), patch.object(
            qwen_asr_local, "model_size", return_value="1.7b"
        ), patch.object(qwen_asr_local, "_align", side_effect=AssertionError("must not align")):
            with self.assertRaisesRegex(ValueError, r"selected recognition language \(English\) may not match the audio.*the probe clips sound like Chinese.*Use auto"):
                self.run_local({"language": "en", "cache": False}, qwen_result=None, real_qwen=True)
        self.assertFalse(Path(asr._2_CLEANED_CHUNKS).exists())

    def test_silent_audio_fails_clearly_without_writing_outputs(self):
        # All-silent audio gives no segments; save_results would otherwise hit KeyError('text').
        with self.assertRaisesRegex(ValueError, "No speech was recognized"):
            self.run_local({}, qwen_result={"language": None, "segments": []})
        self.assertFalse(Path(asr._2_CLEANED_CHUNKS).exists())


if __name__ == "__main__":
    unittest.main()
