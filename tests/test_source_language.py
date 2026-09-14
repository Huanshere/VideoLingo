import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.utils import config_utils as config
from core.spacy_utils import load_nlp_model as nlp
from core import prompts


class SourceLanguageTests(unittest.TestCase):
    def test_manual_selection_updates_both_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("whisper:\n  language: en\n  detected_language: en\n", encoding="utf-8")
            with patch.object(config, "CONFIG_PATH", str(path)):
                config.update_key("whisper.language", "ja")
                self.assertEqual(config.load_key("whisper.detected_language"), "ja")
                config.update_key("whisper.language", "auto")
                self.assertEqual(config.load_key("whisper.detected_language"), "ja")
                config.update_key("whisper.detected_language", "fr")
                self.assertEqual(config.load_key("whisper.language"), "auto")
                self.assertEqual(config.get_source_language(), "fr")

    def test_nlp_uses_explicit_non_english_language_despite_stale_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("whisper:\n  language: ja\n  detected_language: en\n", encoding="utf-8")
            with patch.object(config, "CONFIG_PATH", str(path)), patch.object(nlp.spacy, "load") as load:
                nlp.init_nlp()
                load.assert_called_once_with(nlp.get_spacy_model("ja"))
                self.assertIn("**ja**", prompts.get_split_prompt("Example"))

    def test_unknown_auto_language_requires_transcription(self):
        with patch.object(config, "load_key", return_value={"language": "auto", "detected_language": "auto"}):
            with self.assertRaisesRegex(ValueError, "Run transcription"):
                config.get_source_language()


if __name__ == "__main__":
    unittest.main()
