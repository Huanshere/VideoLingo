"""Contracts at the FonadaLabs transport, timing and speaker boundaries."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import requests

from core import _2_asr as asr
from core.asr_backend import fonada_asr, transcription_cache as cache
from core.asr_backend.audio_preprocess import process_transcription
from core._6_gen_sub import merge_shared_spans

SR = fonada_asr.SAMPLE_RATE


def response(status, body=None, headers=None):
    r = requests.Response()
    r.status_code = status
    r._content = (b"" if body is None else __import__("json").dumps(body).encode())
    r.headers.update(headers or {})
    return r


class Session:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def seconds(*pairs):
    return [(int(a * SR), int(b * SR)) for a, b in pairs]


class CredentialTests(unittest.TestCase):
    def test_missing_key_and_auto_language_fail_before_any_work(self):
        cases = [({"whisper.fonada_api_key": ""}, "fonada_api_key"),
                 ({"whisper.fonada_api_key": "your_key"}, "fonada_api_key"),
                 ({"whisper.fonada_api_key": "k", "whisper.language": "auto"}, "explicit recognition language")]
        for config, expected in cases:
            with self.subTest(config=config), patch.object(
                fonada_asr, "load_key_or", side_effect=lambda key, default, c=config: c.get(key, default)
            ), patch.object(fonada_asr, "load_key", side_effect=lambda key, c=config: c.get(key, "hi")):
                with self.assertRaisesRegex(ValueError, expected):
                    fonada_asr.configured_credentials()


class UtterancePlanTests(unittest.TestCase):
    def test_short_pauses_join_until_the_target_length(self):
        regions = seconds((0, 2), (2.2, 4), (4.3, 5.5), (5.7, 8))
        planned = fonada_asr.plan_utterances(regions, 10 * SR)
        # 0-5.5 fits the 6 s target; 5.7-8 would exceed it and starts a new utterance.
        self.assertEqual(len(planned), 2)
        self.assertLessEqual(planned[0][1], planned[1][0])

    def test_long_pause_or_speaker_change_starts_a_new_utterance(self):
        regions = seconds((0, 1), (2, 3), (3.1, 4))
        self.assertEqual(len(fonada_asr.plan_utterances(regions, 5 * SR)), 2)
        planned = fonada_asr.plan_utterances(regions, 5 * SR, same_speaker=lambda i: i != 1)
        self.assertEqual(len(planned), 3)

    def test_padding_stays_inside_audio_and_never_overlaps(self):
        planned = fonada_asr.plan_utterances(seconds((0.05, 1), (1.6, 2.98)), 3 * SR)
        self.assertEqual(planned[0][0], 0)
        self.assertEqual(planned[-1][1], 3 * SR)
        self.assertLessEqual(planned[0][1], planned[1][0])

    def test_slivers_are_dropped(self):
        self.assertEqual(fonada_asr.plan_utterances(seconds((1, 1.05)), 3 * SR), [])


class TransportTests(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(fonada_asr.time, "sleep")
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(fonada_asr, "check_cancel")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.limiter = type("NoLimit", (), {"wait": lambda self: None, "penalize": lambda self: None})()
        patcher = patch.object(fonada_asr, "rate_limiter", return_value=self.limiter)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_request_sends_file_and_language_and_reads_text(self):
        session = Session(response(200, {"text": " नमस्ते दुनिया ", "transcript_chunks": []}))
        text = fonada_asr.transcribe_clip("secret", "hi", b"RIFF", "0-1s", session)
        self.assertEqual(text, "नमस्ते दुनिया")
        url, kwargs = session.calls[0]
        self.assertEqual(url, "https://api.fonada.ai/v3/asr/transcribe")
        self.assertEqual(kwargs["data"], {"language_id": "hi"})
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertEqual(kwargs["files"]["file"][1], b"RIFF")

    def test_empty_transcript_means_no_speech_not_failure(self):
        session = Session(response(502, {"detail": {"error": "empty_transcript", "message": "x"}}))
        self.assertEqual(fonada_asr.transcribe_clip("k", "en", b"RIFF", "", session), "")
        self.assertEqual(len(session.calls), 1)

    def test_exhausted_credits_are_not_retried_although_status_is_429(self):
        session = Session(response(429, {"detail": {"error": "credits_exhausted"}}))
        with self.assertRaisesRegex(fonada_asr.FonadaError, "credits are exhausted"):
            fonada_asr.transcribe_clip("k", "en", b"RIFF", "", session)
        self.assertEqual(len(session.calls), 1)

    def test_rate_limit_waits_out_the_minute_without_using_attempts(self):
        limited = lambda: response(429, {"detail": {"error": "rate_limit_exceeded",
                                                    "message": "You can make 10 requests per minute."}})
        session = Session(*[limited() for _ in range(fonada_asr.ATTEMPTS + 1)], response(200, {"text": "ok"}))
        self.assertEqual(fonada_asr.transcribe_clip("k", "en", b"RIFF", "", session), "ok")
        self.assertEqual([c.args[0] for c in self.sleep.call_args_list], [60.0] * (fonada_asr.ATTEMPTS + 1))
        session = Session(*[limited() for _ in range(fonada_asr.RATE_LIMIT_WAITS + 1)])
        with self.assertRaisesRegex(fonada_asr.FonadaError, "fonada_requests_per_minute"):
            fonada_asr.transcribe_clip("k", "en", b"RIFF", "", session)

    def test_limiter_allows_n_starts_per_minute(self):
        now = [0.0]
        def sleep(seconds):
            now[0] += seconds
        limiter = fonada_asr.RateLimiter(10, clock=lambda: now[0], sleep=sleep)
        with patch.object(fonada_asr, "check_cancel"):
            starts = []
            for _ in range(25):
                limiter.wait()
                starts.append(now[0])
        self.assertEqual(starts[:10], [0.0] * 10)
        for i in range(10, 25):  # any 10 consecutive starts span at least a minute
            self.assertGreaterEqual(starts[i] - starts[i - 10], 60)

    def test_server_errors_and_timeouts_retry_a_bounded_number_of_times(self):
        session = Session(response(503, {}), requests.Timeout(), response(500, {"detail": {"error": "transcription_failed"}}))
        with self.assertRaisesRegex(fonada_asr.FonadaError, "HTTP 500"):
            fonada_asr.transcribe_clip("k", "en", b"RIFF", "", session)
        self.assertEqual(len(session.calls), fonada_asr.ATTEMPTS)

    def test_client_errors_fail_at_once_without_leaking_the_key(self):
        session = Session(response(401, {"detail": {"error": "invalid_key", "message": "bad key secret-123"}}))
        with self.assertRaises(fonada_asr.FonadaError) as caught:
            fonada_asr.transcribe_clip("secret-123", "en", b"RIFF", "", session)
        self.assertIn("rejected the API key", str(caught.exception))
        self.assertNotIn("secret-123", str(caught.exception))
        self.assertEqual(len(session.calls), 1)

    def test_unsupported_language_names_the_supported_codes(self):
        session = Session(response(400, {"detail": {"error": "unsupported_language"}}))
        with self.assertRaisesRegex(fonada_asr.FonadaError, "does not support language_id 'xx'.*ta"):
            fonada_asr.transcribe_clip("k", "xx", b"RIFF", "", session)

    def test_requests_over_the_25_mb_limit_are_never_sent(self):
        session = Session()
        with self.assertRaisesRegex(fonada_asr.FonadaError, "25000000"):
            fonada_asr.transcribe_clip("k", "en", b"x" * (fonada_asr.MAX_REQUEST_BYTES + 1), "", session)
        self.assertEqual(session.calls, [])

    def test_finished_utterances_are_reused_without_another_request(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            fonada_asr, "CHECKPOINT_DIR", Path(directory)
        ), patch.object(fonada_asr, "transcribe_clip", return_value="hello") as send:
            self.assertEqual(fonada_asr.transcribe_cached("k", "en", b"a", ""), "hello")
            self.assertEqual(fonada_asr.transcribe_cached("k", "en", b"a", ""), "hello")
            self.assertEqual(fonada_asr.transcribe_cached("k", "hi", b"a", ""), "hello")
        self.assertEqual(send.call_count, 2)


class BatchTests(unittest.TestCase):
    def test_each_phrase_gets_its_own_slot_with_silence_around_it(self):
        clips = [np.full(SR, 0.5, np.float32), np.full(2 * SR, 0.25, np.float32)]
        audio = fonada_asr.slot_layout(clips)
        slot, lead = int(24 * SR), int(4 * SR)
        self.assertEqual(len(audio), 2 * slot)
        self.assertTrue((audio[lead:lead + SR] == 0.5).all() and not audio[lead + SR:slot + lead].any())
        self.assertTrue((audio[slot + lead:slot + lead + 2 * SR] == 0.25).all())
        with self.assertRaisesRegex(ValueError, "does not fit"):
            fonada_asr.slot_layout([np.ones(17 * SR, np.float32)])

    def test_chunk_texts_are_assigned_only_when_they_match_the_slots(self):
        body = {"text": "a b", "transcript_chunks": [
            {"idx": 1, "text": " b ", "start_s": 24.0, "end_s": 48.0},
            {"idx": 0, "text": "a", "start_s": 0.0, "end_s": 24.0}]}
        self.assertEqual(fonada_asr.slot_texts(body, 2), ["a", "b"])
        self.assertEqual(fonada_asr.slot_texts(None, 2), ["", ""])
        with self.assertRaisesRegex(fonada_asr.FonadaError, "into 1 chunks"):
            fonada_asr.slot_texts({"transcript_chunks": [{"text": "a b", "start_s": 0}]}, 2)
        shifted = {"transcript_chunks": [{"text": "a", "start_s": 0.0}, {"text": "b", "start_s": 20.5}]}
        with self.assertRaisesRegex(fonada_asr.FonadaError, "starts at 20.50s"):
            fonada_asr.slot_texts(shifted, 2)

    def test_a_batch_is_one_flac_request(self):
        session = Session(response(200, {"text": "x y", "transcript_chunks": [
            {"text": "x", "start_s": 0.0}, {"text": "y", "start_s": 24.0}]}))
        limiter = type("NoLimit", (), {"wait": lambda self: None, "penalize": lambda self: None})()
        with patch.object(fonada_asr, "check_cancel"):
            texts = fonada_asr.transcribe_batch("k", "en", [np.ones(SR, np.float32)] * 2, "", session, limiter)
        self.assertEqual(texts, ["x", "y"])
        name, data, mime = session.calls[0][1]["files"]["file"]
        self.assertEqual((name, mime, data[:4]), ("phrases.flac", "audio/flac", b"fLaC"))


class TimingTests(unittest.TestCase):
    def test_every_word_keeps_the_measured_utterance_span(self):
        segment = fonada_asr.utterance_segment("aaj mausam accha hai", 12.5, 15.0)
        table = process_transcription({"segments": [segment]})
        self.assertEqual(table["text"].tolist(), ["aaj", "mausam", "accha", "hai"])
        self.assertEqual(set(zip(table["start"], table["end"])), {(12.5, 15.0)})

    def test_lines_sharing_an_utterance_become_one_cue(self):
        df = pd.DataFrame({"Source": ["one", "two", "three"], "Translation": ["1", "2", "3"],
                           "timestamp": [(0.0, 4.0), (0.0, 4.0), (5.0, 6.0)]})
        merged = merge_shared_spans(df)
        self.assertEqual(merged["Source"].tolist(), ["one two", "three"])
        self.assertEqual(merged["Translation"].tolist(), ["1 2", "3"])
        self.assertEqual(merged["timestamp"].tolist(), [(0.0, 4.0), (5.0, 6.0)])

    def test_word_timed_lines_are_untouched(self):
        df = pd.DataFrame({"Source": ["a", "b"], "timestamp": [(0.0, 1.0), (1.0, 2.0)]})
        self.assertEqual(merge_shared_spans(df).to_dict("records"), df.to_dict("records"))


class SpeakerTests(unittest.TestCase):
    def test_clusters_are_numbered_by_first_appearance(self):
        a, b = np.array([1.0, 0.0]), np.array([0.0, 1.0])
        self.assertEqual(fonada_asr.cluster_speakers([b, a, b, a], [10] * 4), [0, 1, 0, 1])
        self.assertEqual(fonada_asr.cluster_speakers([a, a * 0.99 + b * 0.01], [10, 10]), [0, 0])
        self.assertEqual(fonada_asr.cluster_speakers([a, b, a], [10] * 3, num_speakers=1), [0, 0, 0])

    def test_short_or_rare_voices_do_not_become_speakers(self):
        a, b, c = np.eye(3)
        # c only appears in short clips; b holds 3 s of 200 s of speech: both join a.
        labels = fonada_asr.cluster_speakers([a, a, b, c, c], [100, 97, 3, 1, 1])
        self.assertEqual(labels, [0, 0, 0, 0, 0])
        # A short clip still joins the nearest real speaker.
        near_b = b * 0.9 + a * 0.1
        labels = fonada_asr.cluster_speakers([a, b, near_b / np.linalg.norm(near_b)], [50, 50, 1])
        self.assertEqual(labels, [0, 1, 1])

    def test_a_voice_change_without_a_pause_cuts_the_region(self):
        a, b = np.array([1.0, 0.0]), np.array([0.0, 1.0])
        audio = np.ones(10 * SR, dtype=np.float32)
        audio[int(5.9 * SR):int(5.92 * SR)] = 0  # quietest frame near the change
        def windows(_audio, starts, length):
            return [a if s + length / 2 < 6 * SR else b for s in starts]
        with patch.object(fonada_asr, "window_embeddings", side_effect=windows):
            regions = fonada_asr.split_speaker_changes(audio, [(0, 10 * SR)])
        self.assertEqual(len(regions), 2)
        self.assertAlmostEqual(regions[0][1] / SR, 5.91, places=2)
        self.assertEqual((regions[0][0], regions[1][1]), (0, 10 * SR))
        with patch.object(fonada_asr, "window_embeddings", side_effect=lambda _a, st, _l: [a] * len(st)):
            self.assertEqual(fonada_asr.split_speaker_changes(audio, [(0, 10 * SR)]), [(0, 10 * SR)])

    def test_labels_replace_embeddings(self):
        segments = [{"text": "x", "start": 0, "end": 20, "speaker_embedding": [1.0, 0.0]},
                    {"text": "y", "start": 20, "end": 40, "speaker_embedding": [0.0, 1.0]},
                    {"text": "z", "start": 40, "end": 41}]
        labelled = fonada_asr.assign_speakers(segments)
        self.assertEqual([s.get("speaker_id") for s in labelled], ["SPEAKER_00", "SPEAKER_01", None])
        self.assertTrue(all("speaker_embedding" not in s for s in labelled))


class PipelineTests(unittest.TestCase):
    def test_fonada_runtime_reaches_the_shared_word_table_with_speakers(self):
        whisper = {"runtime": "fonada", "language": "hi", "model": "large-v3", "cache": False}
        config = {"whisper.runtime": "fonada", "whisper": whisper, "demucs": False}
        part = lambda start, vector: {"language": "hi", "segments": [
            {**fonada_asr.utterance_segment("नमस्ते दोस्तों", start, start + 2), "speaker_embedding": vector}]}
        with patch.object(asr, "load_key", side_effect=config.__getitem__), patch.object(
            asr, "find_media_file", return_value=("input.wav", "audio")
        ), patch.object(asr, "prepare_audio_for_asr"), patch.object(
            asr, "split_audio", return_value=[(0, 1800), (1800, 2000)]
        ), patch.object(asr, "check_cancel"), patch.object(asr, "save_results") as save, patch.object(
            asr, "update_key"
        ), patch.object(fonada_asr, "configured_credentials", return_value=("k", "hi")), patch.object(
            fonada_asr, "transcribe_audio_fonada", side_effect=[part(10, [1, 0]), part(1810, [1, 0])]
        ):
            asr.transcribe.__wrapped__()
        table = save.call_args.args[0]
        self.assertEqual(table["start"].tolist(), [10, 10, 1810, 1810])
        # One speaker across both 30-minute clips: labels are clustered globally.
        self.assertEqual(set(table["speaker_id"]), {"SPEAKER_00"})

    def test_cache_identity_ignores_the_key_and_tracks_speakers(self):
        with tempfile.NamedTemporaryFile(delete=False) as media:
            media.write(b"media")
        self.addCleanup(Path(media.name).unlink)
        base = {"runtime": "fonada", "language": "hi", "model": "large-v3", "fonada_api_key": "a"}
        key = cache.cache_key(media.name, base, False)
        self.assertEqual(key, cache.cache_key(media.name, {**base, "fonada_api_key": "b"}, False))
        self.assertNotEqual(key, cache.cache_key(media.name, {**base, "fonada_num_speakers": 2}, False))
        self.assertNotEqual(key, cache.cache_key(media.name, {**base, "language": "ta"}, False))
        self.assertNotEqual(key, cache.cache_key(media.name, {**base, "runtime": "mai"}, False))


if __name__ == "__main__":
    unittest.main()
