import json
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import soundfile as sf

from dataforge.experiment import (Experiment, fact_score, level, load_corpus,
                                 mix_noise, noise_window, phone_roundtrip, request_audio)

ROOT = Path(__file__).resolve().parents[1]


class AudioTests(unittest.TestCase):
    def test_snr_matches_target_and_does_not_clip(self):
        rng = np.random.default_rng(17)
        speech = level(rng.normal(size=16000), -30)
        noise = rng.normal(size=len(speech))
        for target in (10, 5, 0):
            mixed, actual = mix_noise(speech, noise, target)
            self.assertAlmostEqual(actual, target, places=5)
            self.assertLess(np.max(np.abs(mixed)), 1)

    def test_clipping_and_silence_are_rejected(self):
        with self.assertRaises(ValueError):
            mix_noise(np.zeros(10), np.ones(10), 0)
        with self.assertRaises(ValueError):
            mix_noise(np.ones(10), np.ones(10), 0)

    def test_noise_prefix_identical_for_different_durations(self):
        source = np.arange(7)
        short, looped = noise_window(source, 5, 3)
        long, _ = noise_window(source, 20, 3)
        np.testing.assert_array_equal(short, long[:5])
        self.assertTrue(looped)
        with self.assertRaises(ValueError):
            noise_window(source, 10, 7)

    def test_actual_ffmpeg_pcmu_roundtrip(self):
        try:
            import imageio_ffmpeg
            os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
        t = np.arange(24000) / 24000
        audio = (0.1 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        decoded = phone_roundtrip(audio, 24000)
        self.assertLessEqual(abs(len(decoded) - 8000), 1)
        self.assertGreater(np.corrcoef(decoded, audio[::3])[0, 1], 0.99)

    def test_fact_boundaries_negation_and_explicit_conflicts(self):
        facts = [{"id": "code", "aliases": ["7294"]},
                 {"id": "negation", "aliases": ["Do not cancel"], "forbidden": ["please cancel"]}]
        self.assertEqual(fact_score("7294. Do not cancel.", facts)[0], 1)
        self.assertEqual(fact_score("17294. Cancel.", facts)[0], 0)
        self.assertEqual(fact_score("7294. Do not cancel. Please cancel.", facts)[0], 0.5)
        negative = [{"id": "negation", "aliases": ["Do not cancel"], "negative_proposition": "cancel"}]
        self.assertEqual(fact_score("Do not cancel. Cancel.", negative)[0], 0)
        self.assertEqual(fact_score("Do not cancel.", negative)[0], 1)

    def test_corpus_no_leakage_and_variants_preserve_labeled_facts(self):
        corpus = load_corpus(ROOT / "fixtures/corpus.json")
        self.assertEqual(len(corpus), 30)
        self.assertEqual(sum(x["split"] == "heldout" for x in corpus), 9)
        self.assertEqual(sum(bool(x["facts"]) for x in corpus), 10)

    def test_cell_boundaries_are_three_blank_lines_and_compile(self):
        source = (ROOT / "colab_noise_ab.py").read_text(encoding="utf-8")
        cells = source.split("\n\n\n\n# %%")
        self.assertEqual(len(cells), 15)
        for cell in cells:
            if not cell.startswith("# %%"):
                cell = "# %%" + cell
            compile(cell, "colab_cell", "exec")

    def test_failed_http_is_not_retried(self):
        class Response:
            status_code = 401
            def __enter__(self): return self
            def __exit__(self, *args): pass
        with patch("dataforge.experiment.requests.post", return_value=Response()) as post:
            with self.assertRaisesRegex(RuntimeError, "401"):
                request_audio("TEST_ONLY", {}, "https://example.com")
            self.assertEqual(post.call_count, 1)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        noise = root / "noise.wav"
        sf.write(noise, np.random.default_rng(1).normal(0, 0.05, 8000), 8000)
        config = json.loads((ROOT / "experiment.json").read_text())
        noises = [{"id": name, "path": str(noise), "offset_s": 0, "verified_by_listening": True}
                  for name in ("speech", "traffic")]
        self.exp = Experiment(config, load_corpus(ROOT / "fixtures/corpus.json"), noises, root)

    def tearDown(self):
        self.temp.cleanup()

    def paired_frame(self):
        rows = []
        for variant, recovery, mos in [("baseline", 0.5, 3.5), ("slow", 0.8, 3.45)]:
            for i in range(2):
                rows.append(dict(text_id=str(i), replicate=0, condition="traffic_0dB", variant=variant,
                                 fact_count=2, fact_recovery=recovery, wer=0.1, duration_s=5.0, dnsmos_ovrl=mos))
        return pd.DataFrame(rows)

    def test_paired_comparison_and_missing_pair_rejection(self):
        frame = self.paired_frame()
        self.assertTrue(self.exp.comparisons(frame).iloc[0].screen_pass)
        with self.assertRaises(ValueError):
            self.exp.comparisons(frame.iloc[:-1])

    def test_quality_regression_or_missing_quality_cannot_win(self):
        frame = self.paired_frame()
        frame.loc[frame.variant == "slow", "dnsmos_ovrl"] = 2.0
        self.assertFalse(self.exp.comparisons(frame).iloc[0].screen_pass)
        frame.loc[frame.variant == "slow", "dnsmos_ovrl"] = np.nan
        self.assertFalse(self.exp.comparisons(frame).iloc[0].screen_pass)

    def test_heldout_cannot_run_without_selection(self):
        with self.assertRaises(FileNotFoundError):
            self.exp.run("heldout", ["baseline", "slow"], "TEST_ONLY")

    def test_synthesis_cache_budget_and_corruption(self):
        buffer = io.BytesIO()
        wave = 0.1 * np.sin(2 * np.pi * 440 * np.arange(24000) / 24000)
        sf.write(buffer, wave, 24000, format="WAV")
        metrics = {"client_first_chunk_s": 0.1, "response_complete_s": 0.4}
        item = self.exp.corpus[0]
        with patch("dataforge.experiment.request_audio", return_value=(buffer.getvalue(), metrics)) as post:
            path, first = self.exp.synthesize(item, "baseline", 0, "TEST_ONLY")
            _, second = self.exp.synthesize(item, "baseline", 0, "TEST_ONLY")
            self.assertFalse(first["cached"])
            self.assertTrue(second["cached"])
            self.assertEqual(post.call_count, 1)
            self.exp.config["max_request_characters"] = 1
            with self.assertRaisesRegex(RuntimeError, "budget"):
                self.exp.synthesize(item, "baseline", 1, "TEST_ONLY")
            path.write_bytes(b"damaged")
            with self.assertRaisesRegex(ValueError, "hash"):
                self.exp.synthesize(item, "baseline", 0, "TEST_ONLY")

    def test_scoring_pipeline_resumes_without_retranscribing(self):
        try:
            import imageio_ffmpeg
            os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
        self.exp.config.update(replicates=1, snrs_db=[5])
        self.exp.corpus = [self.exp.corpus[0]]
        buffer = io.BytesIO()
        t = np.arange(24000) / 24000
        sf.write(buffer, 0.1 * np.sin(2 * np.pi * (440 * t + 100 * t*t)), 24000, format="WAV")
        metrics = {"client_first_chunk_s": 0.1, "response_complete_s": 0.4}
        with patch("dataforge.experiment.request_audio", return_value=(buffer.getvalue(), metrics)) as post, \
             patch.object(self.exp, "transcribe", return_value=self.exp.corpus[0]["text"]) as asr, \
             patch.object(self.exp, "quality", return_value={"dnsmos_sig": 3.5, "dnsmos_bak": 3.5, "dnsmos_ovrl": 3.5}):
            first = self.exp.run("dev", ["baseline"], "TEST_ONLY")
            second = self.exp.run("dev", ["baseline"], "TEST_ONLY")
            self.assertEqual(len(first), 3)
            self.assertTrue((first.wer == 0).all())
            self.assertEqual(asr.call_count, 3)
            self.assertEqual(post.call_count, 1)
            self.assertEqual(first.clip_id.tolist(), second.clip_id.tolist())


if __name__ == "__main__":
    unittest.main()
