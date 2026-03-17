"""Unit and integration tests for MiniMax TTS provider."""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from pydub import AudioSegment


class TestMiniMaxTTSUnit(unittest.TestCase):
    """Unit tests for MiniMax TTS provider (no real API calls)."""

    def _make_fake_mp3_hex(self):
        """Create a minimal valid MP3 audio and return its hex string."""
        silence = AudioSegment.silent(duration=100)  # 100ms
        buf = io.BytesIO()
        silence.export(buf, format="mp3")
        return buf.getvalue().hex()

    @patch("core.tts_backend.minimax_tts.requests.post")
    @patch("core.tts_backend.minimax_tts.load_key")
    def test_successful_tts_generation(self, mock_load_key, mock_post):
        """Test that minimax_tts generates a WAV file on successful API response."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": "test-key",
            "minimax_tts.voice": "English_Graceful_Lady",
            "minimax_tts.model": "speech-2.8-hd",
        }[key]

        fake_hex = self._make_fake_mp3_hex()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"audio": fake_hex}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            save_path = f.name

        try:
            minimax_tts("Hello world", save_path)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 0)

            # Verify it's a valid audio file
            audio = AudioSegment.from_wav(save_path)
            self.assertGreater(len(audio), 0)
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    @patch("core.tts_backend.minimax_tts.requests.post")
    @patch("core.tts_backend.minimax_tts.load_key")
    def test_correct_api_request_params(self, mock_load_key, mock_post):
        """Test that the API is called with correct parameters."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": "sk-test-123",
            "minimax_tts.voice": "English_Insightful_Speaker",
            "minimax_tts.model": "speech-2.8-turbo",
        }[key]

        fake_hex = self._make_fake_mp3_hex()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"audio": fake_hex}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            save_path = f.name

        try:
            minimax_tts("Test text", save_path)

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args
            self.assertEqual(call_kwargs.kwargs["headers"]["Authorization"], "Bearer sk-test-123")
            payload = call_kwargs.kwargs["json"]
            self.assertEqual(payload["model"], "speech-2.8-turbo")
            self.assertEqual(payload["text"], "Test text")
            self.assertEqual(payload["voice_setting"]["voice_id"], "English_Insightful_Speaker")
            self.assertFalse(payload["stream"])
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    @patch("core.tts_backend.minimax_tts.load_key")
    def test_invalid_voice_raises_error(self, mock_load_key):
        """Test that an invalid voice ID raises ValueError."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": "test-key",
            "minimax_tts.voice": "NonExistent_Voice",
            "minimax_tts.model": "speech-2.8-hd",
        }[key]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            save_path = f.name

        try:
            with self.assertRaises(Exception):
                minimax_tts("Hello", save_path)
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    @patch("core.tts_backend.minimax_tts.requests.post")
    @patch("core.tts_backend.minimax_tts.load_key")
    def test_missing_audio_data_raises_error(self, mock_load_key, mock_post):
        """Test that missing audio data in response raises ValueError."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": "test-key",
            "minimax_tts.voice": "English_Graceful_Lady",
            "minimax_tts.model": "speech-2.8-hd",
        }[key]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "some error"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            save_path = f.name

        try:
            with self.assertRaises(Exception):
                minimax_tts("Hello", save_path)
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    @patch("core.tts_backend.minimax_tts.requests.post")
    @patch("core.tts_backend.minimax_tts.load_key")
    def test_creates_parent_directories(self, mock_load_key, mock_post):
        """Test that parent directories are created if they don't exist."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": "test-key",
            "minimax_tts.voice": "English_Graceful_Lady",
            "minimax_tts.model": "speech-2.8-hd",
        }[key]

        fake_hex = self._make_fake_mp3_hex()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"audio": fake_hex}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "nested", "dir", "output.wav")
            minimax_tts("Hello", save_path)
            self.assertTrue(os.path.exists(save_path))

    def test_voice_list_not_empty(self):
        """Test that VOICE_LIST contains expected voices."""
        from core.tts_backend.minimax_tts import VOICE_LIST
        self.assertGreater(len(VOICE_LIST), 0)
        self.assertIn("English_Graceful_Lady", VOICE_LIST)
        self.assertIn("Wise_Woman", VOICE_LIST)

    def test_model_list_not_empty(self):
        """Test that MODEL_LIST contains expected models."""
        from core.tts_backend.minimax_tts import MODEL_LIST
        self.assertIn("speech-2.8-hd", MODEL_LIST)
        self.assertIn("speech-2.8-turbo", MODEL_LIST)

    def test_base_url_uses_minimax_io(self):
        """Test that default base URL points to api.minimax.io."""
        from core.tts_backend.minimax_tts import BASE_URL
        self.assertTrue(BASE_URL.startswith("https://api.minimax.io"))


class TestMiniMaxTTSIntegration(unittest.TestCase):
    """Integration tests that call the real MiniMax TTS API.

    Requires MINIMAX_API_KEY environment variable.
    """

    @classmethod
    def setUpClass(cls):
        cls.api_key = os.environ.get("MINIMAX_API_KEY")
        if not cls.api_key:
            raise unittest.SkipTest("MINIMAX_API_KEY not set, skipping integration tests")

    @patch("core.tts_backend.minimax_tts.load_key")
    def test_real_tts_generation(self, mock_load_key):
        """Test TTS generation with a real API call."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": self.api_key,
            "minimax_tts.voice": "English_Graceful_Lady",
            "minimax_tts.model": "speech-2.8-hd",
        }[key]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            save_path = f.name

        try:
            minimax_tts("Hello! Welcome to VideoLingo.", save_path)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)

            # Verify it's valid audio with reasonable duration
            audio = AudioSegment.from_wav(save_path)
            duration_ms = len(audio)
            self.assertGreater(duration_ms, 500)  # At least 0.5 seconds
            self.assertLess(duration_ms, 30000)  # Less than 30 seconds
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    @patch("core.tts_backend.minimax_tts.load_key")
    def test_real_tts_chinese_text(self, mock_load_key):
        """Test TTS generation with Chinese text using Wise_Woman voice."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": self.api_key,
            "minimax_tts.voice": "Wise_Woman",
            "minimax_tts.model": "speech-2.8-hd",
        }[key]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            save_path = f.name

        try:
            minimax_tts("你好！欢迎使用VideoLingo。", save_path)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    @patch("core.tts_backend.minimax_tts.load_key")
    def test_real_tts_turbo_model(self, mock_load_key):
        """Test TTS generation with speech-2.8-turbo model."""
        from core.tts_backend.minimax_tts import minimax_tts

        mock_load_key.side_effect = lambda key: {
            "minimax_tts.api_key": self.api_key,
            "minimax_tts.voice": "English_Insightful_Speaker",
            "minimax_tts.model": "speech-2.8-turbo",
        }[key]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            save_path = f.name

        try:
            minimax_tts("This is a test with the turbo model.", save_path)
            self.assertTrue(os.path.exists(save_path))
            self.assertGreater(os.path.getsize(save_path), 1000)
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)


if __name__ == "__main__":
    unittest.main()
