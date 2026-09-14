import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.tts_backend import sf_fishtts as fish


class SiliconFlowVoiceTests(unittest.TestCase):
    def test_custom_voice_reads_key_and_returns_uri(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "reference.wav"
            audio.write_bytes(b"synthetic reference")
            response = Mock(status_code=200)
            response.json.return_value = {"uri": "speech:test-voice"}
            config = Mock(return_value="test-key")
            with patch.object(fish, "load_key", new=lambda key: config(key)), patch.object(
                fish.requests, "post", return_value=response
            ) as post:
                self.assertEqual(fish.create_custom_voice(audio, "Example", "test"), "speech:test-voice")
            config.assert_called_once_with("sf_fish_tts.api_key")
            self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")
            self.assertEqual(post.call_args.kwargs["json"]["customName"], "test")

    def test_failed_speech_preserves_http_error(self):
        response = Mock(status_code=429, text="Rate limit")
        response.raise_for_status.side_effect = fish.requests.HTTPError("429 Too Many Requests")
        with patch.object(fish, "load_key", return_value={"api_key": "test", "voice": "anna"}), patch.object(
            fish.requests, "post", return_value=response
        ):
            with self.assertRaisesRegex(fish.requests.HTTPError, "429"):
                fish.siliconflow_fish_tts.__wrapped__("Example", "unused.wav")

    def test_missing_voice_uri_is_not_saved_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "reference.wav"
            audio.write_bytes(b"synthetic reference")
            response = Mock(status_code=200)
            response.json.return_value = {}
            with patch.object(fish, "load_key", new=lambda key: "test-key"), patch.object(
                fish.requests, "post", return_value=response
            ):
                with self.assertRaisesRegex(ValueError, "voice URI"):
                    fish.create_custom_voice(audio, "Example")


if __name__ == "__main__":
    unittest.main()
