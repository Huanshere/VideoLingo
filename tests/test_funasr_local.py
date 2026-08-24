import importlib
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from ruamel.yaml import YAML

from core.asr_backend.audio_preprocess import process_transcription

funasr_local = importlib.import_module("core.asr_backend.funasr_local")


class FakeModel:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.results


class FunASRLocalTest(unittest.TestCase):
    def setUp(self):
        funasr_local.clear_model_cache()

    def tearDown(self):
        funasr_local.clear_model_cache()

    def assert_overlong_token_is_preserved(
        self,
        result,
        offset_seconds,
        clip_duration_seconds,
        expected_times,
    ):
        token = result["text"]
        segments = funasr_local._segments_from_results(
            [result],
            offset_seconds=offset_seconds,
            clip_duration_seconds=clip_duration_seconds,
        )

        rows = process_transcription({"segments": segments}).to_dict("records")

        expected_chunks = [
            token[index : index + 30] for index in range(0, len(token), 30)
        ]
        self.assertEqual([row["text"] for row in rows], expected_chunks)
        self.assertEqual("".join(row["text"] for row in rows), token)
        self.assertTrue(all(len(row["text"]) <= 30 for row in rows))
        for row, (expected_start, expected_end) in zip(rows, expected_times):
            self.assertAlmostEqual(row["start"], expected_start)
            self.assertAlmostEqual(row["end"], expected_end)

    def test_aligned_words_apply_clip_offset(self):
        result = {
            "words": ["你", "好", "。"],
            "timestamp": [[100, 300], [320, 520], [520, 580]],
        }

        words = funasr_local.aligned_words(result, offset_seconds=30.0)

        self.assertEqual(
            words,
            [
                {"word": "你", "start": 30.1, "end": 30.3},
                {"word": "好", "start": 30.32, "end": 30.52},
                {"word": "。", "start": 30.52, "end": 30.58},
            ],
        )

    def test_aligned_words_reject_partial_alignment(self):
        result = {"words": ["hello", "world"], "timestamp": [[0, 200]]}

        self.assertEqual(funasr_local.aligned_words(result, 0.0), [])

    def test_fallback_words_cover_clip_without_oversized_tokens(self):
        result = {"text": "<|zh|><|NEUTRAL|><|Speech|><|withitn|>你好世界。"}

        words = funasr_local.fallback_words(
            result,
            offset_seconds=10.0,
            clip_duration_seconds=5.0,
        )

        self.assertEqual(
            [word["word"] for word in words], ["你", "好", "世", "界", "。"]
        )
        self.assertEqual(words[0]["start"], 10.0)
        self.assertEqual(words[-1]["end"], 15.0)
        self.assertTrue(all(len(word["word"]) <= 30 for word in words))

    def test_native_overlong_token_survives_process_transcription(self):
        token = "n" * 61

        self.assert_overlong_token_is_preserved(
            {
                "text": token,
                "words": [token],
                "timestamp": [[1000, 7100]],
            },
            offset_seconds=10.0,
            clip_duration_seconds=8.0,
            expected_times=[(11.0, 14.0), (14.0, 17.0), (17.0, 17.1)],
        )

    def test_fallback_overlong_token_survives_process_transcription(self):
        token = "f" * 61

        self.assert_overlong_token_is_preserved(
            {"text": token},
            offset_seconds=20.0,
            clip_duration_seconds=6.1,
            expected_times=[
                (20.0, 23.0),
                (23.0, 26.0),
                (26.0, 26.1),
            ],
        )

    def test_transcribe_audio_returns_whisperx_contract(self):
        model = FakeModel(
            [
                {
                    "text": "<|en|><|NEUTRAL|><|Speech|><|withitn|>Hello world.",
                    "words": ["Hello", "world", "."],
                    "timestamp": [[100, 400], [500, 900], [900, 950]],
                }
            ]
        )
        config = {
            "funasr.model": "iic/SenseVoiceSmall",
            "funasr.device": "cpu",
            "whisper.language": "en",
        }

        with (
            patch.object(funasr_local, "load_key", side_effect=config.__getitem__),
            patch.object(funasr_local, "update_key") as update_key,
            patch.object(funasr_local, "get_model", return_value=model),
            patch.object(
                funasr_local, "get_inference_lock", return_value=threading.Lock()
            ),
            patch.object(
                funasr_local, "extract_audio_segment"
            ) as extract_audio_segment,
        ):
            result = funasr_local.transcribe_audio(
                "raw.mp3",
                "vocals.mp3",
                start=20.0,
                end=25.0,
            )

        extract_audio_segment.assert_called_once()
        self.assertEqual(result["language"], "en")
        self.assertEqual(len(result["segments"]), 1)
        segment = result["segments"][0]
        self.assertEqual(segment["text"], "Hello world.")
        self.assertEqual(segment["start"], 20.1)
        self.assertEqual(segment["end"], 20.95)
        self.assertEqual(
            segment["words"][1], {"word": "world", "start": 20.5, "end": 20.9}
        )
        self.assertEqual(model.calls[0]["language"], "en")
        self.assertTrue(str(model.calls[0]["input"]).endswith(".wav"))
        update_key.assert_called_once_with("whisper.detected_language", "en")

    def test_unsupported_language_fails_before_model_load(self):
        config = {
            "funasr.model": "iic/SenseVoiceSmall",
            "funasr.device": "auto",
            "whisper.language": "fr",
        }

        with (
            patch.object(funasr_local, "load_key", side_effect=config.__getitem__),
            patch.object(funasr_local, "get_model") as get_model,
        ):
            with self.assertRaisesRegex(ValueError, "supports zh, en, and ja"):
                funasr_local.transcribe_audio("raw.mp3", "raw.mp3", 0.0, 1.0)

        get_model.assert_not_called()

    def test_missing_optional_dependency_has_install_command(self):
        real_import = importlib.import_module

        def import_module(name, *args, **kwargs):
            if name == "funasr":
                raise ImportError("missing")
            return real_import(name, *args, **kwargs)

        with patch.object(
            funasr_local.importlib, "import_module", side_effect=import_module
        ):
            with self.assertRaisesRegex(RuntimeError, "installer.py --with-funasr"):
                funasr_local.create_model("iic/SenseVoiceSmall", "cpu")


class InstallerWiringTest(unittest.TestCase):
    def test_config_declares_funasr_defaults(self):
        with Path("config.yaml").open(encoding="utf-8") as config_file:
            config = YAML(typ="safe").load(config_file)

        self.assertEqual(config["funasr"]["model"], "iic/SenseVoiceSmall")
        self.assertEqual(config["funasr"]["device"], "auto")

    def test_parser_exposes_optional_funasr_install(self):
        installer = importlib.import_module("installer")

        args = installer.build_parser().parse_args(["--with-funasr"])

        self.assertTrue(args.with_funasr)

    def test_optional_install_uses_bounded_funasr_requirement(self):
        installer = importlib.import_module("installer")

        with (
            patch.object(installer, "package_version", return_value=None),
            patch.object(installer, "pip_install") as pip_install,
        ):
            installer.install_funasr()

        pip_install.assert_called_once_with(["funasr>=1.3.9,<2"], retries=3)

    def test_optional_install_upgrades_incompatible_funasr(self):
        installer = importlib.import_module("installer")

        with (
            patch.object(installer, "package_version", return_value="1.2.0"),
            patch.object(installer, "pip_install") as pip_install,
        ):
            installer.install_funasr()

        pip_install.assert_called_once_with(["funasr>=1.3.9,<2"], retries=3)

    def test_optional_requirement_does_not_invalidate_base_install_state(self):
        installer = importlib.import_module("installer")
        base_hash = installer.requirements_hash()

        with patch.object(installer, "FUNASR_REQUIREMENT", "funasr>=999"):
            self.assertEqual(installer.requirements_hash(), base_hash)

    def test_launcher_reads_selected_asr_runtime(self):
        launch = importlib.import_module("launch")

        self.assertEqual(launch.configured_asr_runtime(), "local")

    def test_launcher_import_survives_missing_yaml_dependency(self):
        launch = importlib.import_module("launch")
        self.addCleanup(importlib.reload, launch)

        with patch.dict(sys.modules, {"yaml": None}):
            reloaded = importlib.reload(launch)

            self.assertEqual(reloaded.configured_asr_runtime(), "local")


if __name__ == "__main__":
    unittest.main()
