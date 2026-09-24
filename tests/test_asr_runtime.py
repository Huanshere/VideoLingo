import unittest
from unittest.mock import patch

from core import _2_asr as asr


class RuntimeTests(unittest.TestCase):
    def test_unknown_runtime_fails_before_preparing_audio(self):
        with patch.object(asr, "load_key", return_value="cloud"), patch.object(
            asr, "find_media_file"
        ) as find:
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                asr.transcribe.__wrapped__()
            find.assert_not_called()

    def test_supported_runtimes_reach_media_discovery(self):
        for runtime in ("local", "elevenlabs", "mai"):
            with self.subTest(runtime=runtime), patch.object(asr, "load_key", return_value=runtime), patch.object(
                asr, "find_media_file", side_effect=FileNotFoundError("synthetic missing input")
            ):
                with self.assertRaisesRegex(FileNotFoundError, "synthetic missing input"):
                    asr.transcribe.__wrapped__()


if __name__ == "__main__":
    unittest.main()
