"""Contracts at the Azure MAI transport and response boundary."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

from core.asr_backend import mai_asr
from core.utils import config_utils


RESPONSE = {
    "phrases": [{
        "text": "Hello world.", "locale": "en-US",
        "words": [
            {"text": "Hello", "offsetMilliseconds": 200, "durationMilliseconds": 300},
            {"text": "world.", "offsetMilliseconds": 600, "durationMilliseconds": 400},
        ],
    }],
}


class MaiAsrTests(unittest.TestCase):
    def test_word_timestamps_and_language_survive_conversion(self):
        converted = mai_asr.mai2whisper(RESPONSE, offset=30)
        self.assertEqual(converted["language"], "en")
        self.assertEqual(
            [(word["word"], word["start"], word["end"])
             for word in converted["segments"][0]["words"]],
            [("Hello", 30.2, 30.5), ("world.", 30.6, 31.0)],
        )

    def test_definition_requests_clean_word_timestamps(self):
        definition = mai_asr.request_definition("auto")
        self.assertNotIn("locales", definition)
        self.assertEqual(definition["enhancedMode"], {
            "enabled": True,
            "model": "MAI-Transcribe-2",
            "modelOptions": {"timestamps": "word", "transcribeStyle": "clean"},
        })
        self.assertEqual(mai_asr.request_definition("ja")["locales"], ["ja"])

    def test_resource_endpoint_cannot_send_audio_and_key_to_another_host(self):
        self.assertEqual(
            mai_asr.transcription_url("https://example.cognitiveservices.azure.com/"),
            "https://example.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe?api-version=2025-10-15",
        )
        for endpoint in ("https://example.com", "https://example.cognitiveservices.azure.com.evil.test",
                         "https://example.cognitiveservices.azure.com/path"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                mai_asr.transcription_url(endpoint)

    def test_legacy_config_detects_region_and_retries_transient_errors(self):
        class Reply:
            def __init__(self, status, body=None):
                self.status_code = status
                self.ok = status == 200
                self.text = "unavailable" if status != 200 else ""
                self.body = body

            def json(self):
                return self.body

        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            config.write_text("whisper:\n  language: en\n  mai_api_key: test-key\n", encoding="utf-8")
            responses = [requests.ConnectionError("dropped"), Reply(503), Reply(200, RESPONSE)]
            with patch.object(config_utils, "CONFIG_PATH", str(config)), patch.object(
                mai_asr, "detect_region", return_value="westus2"
            ), patch.object(mai_asr, "audio_slice_wav", return_value=b"RIFF"), patch.object(
                mai_asr, "check_cancel"
            ), patch.object(mai_asr.time, "sleep"), patch.object(
                mai_asr.requests, "post", side_effect=responses
            ) as post:
                converted = mai_asr.transcribe_audio_mai("raw", "vocal", 30, 35)
            self.assertEqual(converted["segments"][0]["words"][0]["start"], 30.2)
            self.assertEqual(config_utils.yaml.load(config.read_text())["whisper"]["mai_region"], "westus2")
            self.assertEqual(post.call_count, 3)
            self.assertTrue(all("westus2.api.cognitive.microsoft.com" in call.args[0]
                                for call in post.call_args_list))
            submitted = json.loads(post.call_args.kwargs["files"]["definition"][1])
            self.assertEqual(submitted["locales"], ["en"])


if __name__ == "__main__":
    unittest.main()
