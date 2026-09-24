import json
import unittest
from unittest.mock import patch

from core.asr_backend import mai_asr


SAMPLE = {
    "durationMilliseconds": 5000,
    "phrases": [
        {
            "offsetMilliseconds": 0,
            "durationMilliseconds": 5000,
            "text": "So with that.",
            "locale": "en-US",
            "words": [
                {"text": "So", "offsetMilliseconds": 1600, "durationMilliseconds": 119},
                {"text": "with", "offsetMilliseconds": 1800, "durationMilliseconds": 119},
                {"text": " ", "offsetMilliseconds": 1900, "durationMilliseconds": 10},
                {"text": "that.", "offsetMilliseconds": 1960, "durationMilliseconds": 140},
            ],
        },
        {"text": "", "words": []},
    ],
}


class MaiConversionTests(unittest.TestCase):
    def test_words_become_offset_seconds(self):
        result = mai_asr.mai2whisper(SAMPLE, offset=30.0)
        self.assertEqual(result["language"], "en")
        self.assertEqual(len(result["segments"]), 1)
        seg = result["segments"][0]
        self.assertEqual([w["word"] for w in seg["words"]], ["So", "with", "that."])
        self.assertAlmostEqual(seg["words"][0]["start"], 31.6)
        self.assertAlmostEqual(seg["words"][0]["end"], 31.719)
        self.assertAlmostEqual(seg["start"], 31.6)
        self.assertAlmostEqual(seg["end"], 32.1)

    def test_empty_response(self):
        self.assertEqual(mai_asr.mai2whisper({}), {"segments": [], "language": None})

    def test_definition_requests_word_timestamps_and_optional_locale(self):
        auto = mai_asr.request_definition("auto")
        self.assertEqual(auto["enhancedMode"]["model"], "MAI-Transcribe-2")
        self.assertEqual(auto["enhancedMode"]["modelOptions"]["timestamps"], "word")
        self.assertNotIn("locales", auto)
        self.assertEqual(mai_asr.request_definition("ja")["locales"], ["ja"])

    def test_url_from_region_or_full_endpoint(self):
        self.assertEqual(
            mai_asr.transcription_url("EastUS"),
            "https://eastus.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe?api-version=2025-10-15",
        )
        self.assertEqual(
            mai_asr.transcription_url("https://x.cognitiveservices.azure.com/"),
            "https://x.cognitiveservices.azure.com/speechtotext/transcriptions:transcribe?api-version=2025-10-15",
        )
        for bad in ("", "x.cognitiveservices.azure.com", "east us"):
            with self.assertRaises(ValueError):
                mai_asr.transcription_url(bad)

    def test_detect_region_returns_the_region_that_accepts_the_key(self):
        class Resp:
            def __init__(self, status):
                self.status_code = status

        def post(url, **kwargs):
            if "westus2." in url:
                return Resp(200)
            if "northeurope." in url:
                raise mai_asr.requests.ConnectionError("offline")
            return Resp(401)

        with patch.object(mai_asr.requests, "post", side_effect=post) as calls:
            self.assertEqual(mai_asr.detect_region("k"), "westus2")
        self.assertEqual(calls.call_count, len(mai_asr.REGIONS))
        self.assertTrue(all("/sts/v1.0/issueToken" in c.args[0] for c in calls.call_args_list))
        with patch.object(mai_asr.requests, "post", return_value=Resp(401)):
            self.assertIsNone(mai_asr.detect_region("k"))
        self.assertIsNone(mai_asr.detect_region("  "))

    def test_http_error_is_raised_with_body(self):
        class Resp:
            ok, status_code, text = False, 401, "denied"

        keys = {"whisper.language": "en", "whisper.mai_region": "eastus", "whisper.mai_api_key": "k"}
        with patch.object(mai_asr, "audio_slice_wav", return_value=b"RIFF"), patch.object(
            mai_asr, "load_key", side_effect=keys.get
        ), patch.object(mai_asr, "load_key_or", side_effect=lambda k, d: keys.get(k, d)), patch.object(
            mai_asr.requests, "post", return_value=Resp()
        ) as post:
            with self.assertRaisesRegex(RuntimeError, "HTTP 401 denied"):
                mai_asr.transcribe_audio_mai("raw", "vocal", 0, 5)
            definition = json.loads(post.call_args.kwargs["files"]["definition"][1])
            self.assertEqual(definition["locales"], ["en"])
            self.assertEqual(post.call_count, 1)

    def test_transient_failures_are_retried(self):
        class Resp:
            def __init__(self, status, body):
                self.ok, self.status_code, self.text, self._body = status == 200, status, "", body

            def json(self):
                return self._body

        keys = {"whisper.language": "en", "whisper.mai_region": "eastus", "whisper.mai_api_key": "k"}
        replies = [mai_asr.requests.ConnectionError("dropped"), Resp(503, None), Resp(200, SAMPLE)]
        with patch.object(mai_asr, "audio_slice_wav", return_value=b"RIFF"), patch.object(
            mai_asr, "load_key", side_effect=keys.get
        ), patch.object(mai_asr, "load_key_or", side_effect=lambda k, d: keys.get(k, d)), patch.object(
            mai_asr, "update_key"
        ), patch.object(mai_asr.time, "sleep"), patch.object(
            mai_asr.requests, "post", side_effect=replies
        ) as post:
            result = mai_asr.transcribe_audio_mai("raw", "vocal", 0, 5)
        self.assertEqual(post.call_count, 3)
        self.assertEqual(result["language"], "en")

    def test_empty_region_is_detected_and_saved_before_transcribing(self):
        keys = {"whisper.language": "en", "whisper.mai_region": "", "whisper.mai_api_key": "k"}
        with patch.object(mai_asr, "audio_slice_wav", return_value=b"RIFF"), patch.object(
            mai_asr, "load_key", side_effect=keys.get
        ), patch.object(mai_asr, "load_key_or", side_effect=lambda k, d: keys.get(k, d)), patch.object(
            mai_asr, "detect_region", return_value=None
        ):
            with self.assertRaisesRegex(ValueError, "not accepted"):
                mai_asr.transcribe_audio_mai("raw", "vocal", 0, 5)
        with patch.object(mai_asr, "load_key", side_effect=keys.get), patch.object(
            mai_asr, "load_key_or", side_effect=lambda k, d: keys.get(k, d)
        ), patch.object(mai_asr, "detect_region", return_value="westus"), patch.object(
            mai_asr, "update_key"
        ) as save, patch.object(mai_asr, "audio_slice_wav", return_value=b"RIFF"), patch.object(
            mai_asr.requests, "post", side_effect=RuntimeError("stop")
        ) as post:
            with self.assertRaisesRegex(RuntimeError, "stop"):
                mai_asr.transcribe_audio_mai("raw", "vocal", 0, 5)
        save.assert_any_call("whisper.mai_region", "westus")
        self.assertIn("https://westus.api.cognitive.microsoft.com", post.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
