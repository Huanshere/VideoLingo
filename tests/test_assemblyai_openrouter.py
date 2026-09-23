import unittest
from unittest.mock import Mock, patch

from core.asr_backend import assemblyai_openrouter as backend


class PlanChunksTests(unittest.TestCase):
    def test_short_interval_is_one_window(self):
        self.assertEqual(backend.plan_fixed_chunks(0, 90), [(0.0, 90.0)])
        self.assertEqual(backend.plan_fixed_chunks(0, 120), [(0.0, 120.0)])

    def test_ten_minute_audio_stays_under_sync_limit(self):
        windows = backend.plan_fixed_chunks(0, 600)
        self.assertGreater(len(windows), 1)
        for start, end in windows:
            self.assertLessEqual(end - start, backend.MAX_SYNC_SECONDS)
            self.assertGreater(end, start)
        self.assertEqual(windows[0][0], 0.0)
        self.assertEqual(windows[-1][1], 600.0)
        for previous, current in zip(windows, windows[1:]):
            self.assertLessEqual(current[0], previous[1])

    def test_rejects_empty_interval(self):
        with self.assertRaises(ValueError):
            backend.plan_fixed_chunks(10, 10)


class ParseAndStitchTests(unittest.TestCase):
    def test_openrouter_words_and_assemblyai_milliseconds(self):
        openrouter = {
            "language": "english",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.4},
                {"word": "world", "start": 0.4, "end": 0.8},
            ],
        }
        words = backend.extract_words(openrouter)
        self.assertEqual(backend.normalize_language(openrouter), "en")
        self.assertEqual(words[0]["word"], "Hello")
        self.assertEqual(words[1]["end"], 0.8)

        assembly = {
            "language_code": "eng",
            "words": [
                {"text": "Hello", "start": 0, "end": 400},
                {"text": "world", "start": 400, "end": 800},
            ],
        }
        converted = backend.extract_words(assembly)
        self.assertEqual(converted[0]["start"], 0.0)
        self.assertEqual(converted[1]["end"], 0.8)
        self.assertEqual(backend.normalize_language(assembly), "en")

    def test_stitch_drops_overlap_and_adds_absolute_offsets(self):
        first = backend.shift_words(
            [{"word": "one", "start": 0.0, "end": 0.3}, {"word": "two", "start": 109.2, "end": 109.6}],
            0.0,
        )
        second = backend.shift_words(
            [{"word": "two", "start": 0.2, "end": 0.6}, {"word": "three", "start": 1.5, "end": 2.0}],
            109.0,
        )
        merged = backend.stitch_word_lists([(0.0, first), (110.0, second)])
        self.assertEqual([word["word"] for word in merged], ["one", "two", "three"])
        self.assertEqual(merged[2]["start"], 110.5)
        self.assertEqual(merged[2]["end"], 111.0)

    def test_words_match_step2_segment_shape(self):
        words = [
            {"word": "Hello", "start": 1.0, "end": 1.2, "speaker_id": "SPEAKER_0"},
            {"word": "there", "start": 1.2, "end": 1.5, "speaker_id": "SPEAKER_0"},
            {"word": "Later", "start": 4.0, "end": 4.3, "speaker_id": "SPEAKER_1"},
        ]
        result = backend.words_to_whisper(words, language="en")
        self.assertEqual(result["language"], "en")
        self.assertEqual(len(result["segments"]), 2)
        first = result["segments"][0]
        self.assertEqual(first["text"], "Hello there")
        self.assertEqual(first["start"], 1.0)
        self.assertEqual(first["end"], 1.5)
        self.assertEqual(first["words"][0]["word"], "Hello")
        self.assertIn("start", first["words"][0])
        self.assertIn("end", first["words"][0])


class TranscribeAudioTests(unittest.TestCase):
    def test_multi_minute_interval_chunks_and_stitches(self):
        windows = [(0.0, 110.0), (109.0, 219.0), (218.0, 250.0)]
        responses = [
            {"language": "en", "words": [{"word": "alpha", "start": 0.1, "end": 0.4}]},
            {"language": "en", "words": [{"word": "beta", "start": 1.2, "end": 1.5}]},
            {"language": "en", "words": [{"word": "gamma", "start": 2.0, "end": 2.3}]},
        ]
        posted = []

        def fake_post(url, json=None, headers=None, timeout=None):
            posted.append({"url": url, "json": json, "headers": headers})
            response = Mock()
            response.status_code = 200
            response.ok = True
            response.json.return_value = responses[len(posted) - 1]
            return response

        with patch.object(backend, "plan_chunks_for_file", return_value=windows), patch.object(
            backend, "audio_slice_wav", return_value=b"RIFF....wav"
        ) as slice_wav, patch.object(backend, "load_key_or", side_effect=self._config), patch.object(
            backend, "update_key"
        ), patch.object(backend, "check_cancel"), patch.object(
            backend.requests, "post", side_effect=fake_post
        ), patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-openrouter-key"}):
            result = backend.transcribe_audio_assemblyai("raw.mp3", "vocal.mp3", 0, 250)

        self.assertEqual(slice_wav.call_count, 3)
        for call_item, (window_start, window_end) in zip(slice_wav.call_args_list, windows):
            start, end = call_item.args[1], call_item.args[2]
            self.assertLessEqual(end - start, backend.MAX_SYNC_SECONDS)
            self.assertEqual((start, end), (window_start, window_end))
        self.assertEqual(len(posted), 3)
        self.assertTrue(posted[0]["url"].endswith("/audio/transcriptions"))
        self.assertEqual(posted[0]["json"]["model"], "assemblyai/universal-3-5-pro")
        self.assertEqual(posted[0]["json"]["input_audio"]["format"], "wav")
        self.assertIn("data", posted[0]["json"]["input_audio"])
        self.assertEqual(posted[0]["headers"]["Authorization"], "Bearer test-openrouter-key")
        words = [word["word"] for segment in result["segments"] for word in segment["words"]]
        self.assertEqual(words, ["alpha", "beta", "gamma"])
        self.assertAlmostEqual(result["segments"][1]["start"], 110.2)
        self.assertAlmostEqual(result["segments"][2]["start"], 220.0)
        self.assertEqual(result["language"], "en")

    def test_rejects_oversized_chunk(self):
        with patch.object(backend, "plan_chunks_for_file", return_value=[(0.0, 130.0)]), patch.object(
            backend, "load_key_or", return_value="auto"
        ), patch.object(backend, "check_cancel"):
            with self.assertRaisesRegex(ValueError, "120"):
                backend.transcribe_audio_assemblyai("raw.mp3", "vocal.mp3", 0, 130)

    @staticmethod
    def _config(key, default=None):
        values = {
            "whisper.openrouter_api_key": "",
            "whisper.openrouter_base_url": "https://openrouter.ai/api/v1",
            "whisper.assemblyai_model": "assemblyai/universal-3-5-pro",
            "whisper.language": "en",
            "api.key": "YOUR_API_KEY",
            "api.base_url": "https://openrouter.ai/api/v1",
        }
        return values.get(key, default)


if __name__ == "__main__":
    unittest.main()
