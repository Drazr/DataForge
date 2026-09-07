import json
import io
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import soundfile as sf

from dataforge.experiment import (Experiment, fact_score, level, load_corpus,
                                 mix_noise, noise_window, phone_roundtrip, request_audio,
                                 active_rms, level_active, validate_challenges, save_json)

ROOT = Path(__file__).resolve().parents[1]


class AudioTests(unittest.TestCase):
    def test_added_silence_does_not_raise_active_speech_gain(self):
        speech = 0.1 * np.sin(2 * np.pi * 440 * np.arange(8000) / 8000)
        padded = np.concatenate([speech, np.zeros(8000)])
        short = level_active(speech, -26)
        long = level_active(padded, -26)
        np.testing.assert_allclose(short, long[:8000])
        self.assertAlmostEqual(20 * np.log10(active_rms(long)), -26)
        with self.assertRaisesRegex(ValueError, "Silent"):
            active_rms(np.zeros(100))

    def test_noise_gain_is_identical_across_variant_durations(self):
        source = np.random.default_rng(3).normal(0, 0.03, 16000)
        source[8000:] *= 2
        speech = level_active(np.sin(2 * np.pi * 440 * np.arange(8000) / 8000), -26)
        longer = np.concatenate([speech, np.zeros(8000)])
        reference = float(np.sqrt(np.mean(source ** 2)))
        short_mix, _ = mix_noise(speech, source[:8000], 5,
                                speech_reference_rms=active_rms(speech), noise_reference_rms=reference)
        long_mix, measured = mix_noise(longer, source, 5,
                                      speech_reference_rms=active_rms(longer), noise_reference_rms=reference)
        np.testing.assert_allclose(short_mix, long_mix[:8000], atol=1e-7)
        self.assertAlmostEqual(measured, 5)

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
        self.assertEqual(len(cells), 16)
        self.assertEqual(len(re.findall(r"^# %% Cell ", source, re.M)), 16)
        self.assertEqual(re.findall(r"^# %% Cell (\d+)", source, re.M), list(map(str, range(1, 17))))
        for boundary in re.finditer(r"\n+# %%", source):
            self.assertEqual(boundary.group().count("\n"), 4)
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

    def test_finer_grid_reuses_audio_and_keeps_cumulative_budget(self):
        buffer = io.BytesIO()
        sf.write(buffer, 0.1 * np.sin(np.arange(24000)), 24000, format="WAV")
        item = self.exp.corpus[0]
        with patch("dataforge.experiment.request_audio", return_value=(buffer.getvalue(), {})) as post:
            path, _ = self.exp.synthesize(item, "baseline", 0, "TEST_ONLY")
            config = self.exp.config | {"snrs_db": [10, 7.5, 5, 2.5, 0]}
            refined = Experiment(config, self.exp.corpus, self.exp.noises, self.temp.name)
            self.assertNotEqual(self.exp.root, refined.root)
            reused, meta = refined.synthesize(item, "baseline", 0, "TEST_ONLY")
            self.assertEqual(path, reused)
            self.assertTrue(meta["cached"])
            self.assertEqual(post.call_count, 1)
            self.assertEqual(self.exp.ledger_path, refined.ledger_path)
            refined.config["max_request_characters"] = len(item["text"])
            with self.assertRaisesRegex(RuntimeError, "budget"):
                refined.synthesize(item, "baseline", 1, "TEST_ONLY")

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

    def test_baseline_selection_heldout_and_analysis_exports(self):
        """Real codec/files/scoring/selection, with external inference stubbed."""
        from dataforge.reporting import export_baseline
        try:
            import imageio_ffmpeg
            os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
        dev = [x for x in self.exp.corpus if x["split"] == "dev" and x["facts"]][:2]
        heldout = [x for x in self.exp.corpus if x["split"] == "heldout" and x["facts"]][:1]
        experiment = Experiment(self.exp.config | {"snrs_db": [10, 5]}, dev + heldout,
                                self.exp.noises, self.temp.name)
        buffer = io.BytesIO()
        t = np.arange(24000) / 24000
        sf.write(buffer, 0.1 * np.sin(2 * np.pi * (440 * t + 100 * t*t)), 24000, format="WAV")

        def transcript(path):
            item = next(x for x in experiment.corpus if Path(path).stem.startswith(x["id"] + "_"))
            suffix = Path(path).stem[len(item["id"]) + 1:]
            variant = suffix.split("_", 1)[0]
            if variant == "baseline" and not suffix.endswith("_clean"):
                return "unintelligible"
            return experiment.variant(item, variant)[0]

        with patch("dataforge.experiment.request_audio", return_value=(buffer.getvalue(), {"client_first_chunk_s": 0.1})), \
             patch.object(experiment, "transcribe", side_effect=transcript), \
             patch.object(experiment, "quality", return_value={"dnsmos_sig": 3.5, "dnsmos_bak": 3.5, "dnsmos_ovrl": 3.5}):
            baseline = experiment.run("dev", ["baseline"], "TEST_ONLY")
            export_baseline(baseline, experiment.root, replicates=2)
            conditions = ["speech_5dB"]
            evidence = validate_challenges(baseline, conditions, 2)
            self.assertEqual(evidence.text_id.nunique(), 2)
            save_json(experiment.root / "challenge.json", {"conditions": conditions})
            experiment.run("dev", ["slow"], "TEST_ONLY")
            selection = experiment.select(conditions, {"slow": {"facts_preserved": True, "quality_acceptable": True}})
            self.assertEqual(selection["variant"], "slow")
            final = experiment.run("heldout", ["baseline", "slow"], "TEST_ONLY")
            self.assertTrue(experiment.comparisons(final, conditions).iloc[0].screen_pass)
            exported = pd.read_csv(experiment.root / "baseline_results.csv")
            for field in ("run_id", "replicate", "snr_db", "measured_snr_db", "wer", "fact_recovery",
                          "estoi", "dnsmos_ovrl", "speech_level_method", "noise_kind", "audio_path"):
                self.assertIn(field, exported.columns)
            self.assertTrue((exported.run_id == experiment.fingerprint).all())
            self.assertTrue((experiment.root / "noise_failure_evidence.csv").is_file())
            # Exercise the new consumer against actual producer schemas/serialization.
            from dataforge.grid_analysis import run_analysis
            save_json(experiment.root / "evidence_scope.json", {
                "synthesis_repeats": 2, "snrs_db": [10, 5], "noise_sources": 2,
                "texts_by_split": {"dev": len(dev), "heldout": len(heldout)},
                "critical_texts_by_split": {"dev": len(dev), "heldout": len(heldout)},
            })
            settings = json.loads((ROOT / "grid_analysis.json").read_text())
            settings["bootstrap_samples"] = 100
            analysis = run_analysis(experiment.root, settings, experiment.root / "grid-analysis")
            self.assertEqual(analysis["report"]["missing_rows"], 0)
            self.assertEqual(analysis["report"]["grid_source"], "baseline_condition_summary.csv")
            self.assertEqual(len(analysis["intervals"]), 6)
            self.assertFalse(analysis["intervals"].supported_breakpoint.any())


class ChallengeTests(unittest.TestCase):
    def baseline(self):
        rows = []
        for text in ("A", "B"):
            for rep in (0, 1):
                for condition in ("clean", "speech_5dB"):
                    rows.append(dict(text_id=text, replicate=rep, condition=condition,
                                     split="dev", variant="baseline", clip_id=f"{text}_{rep}_{condition}",
                                     audio_path="clip.wav", fact_details={
                                         "code": {"recovered": condition == "clean", "conflict": False}}))
        return pd.DataFrame(rows)

    def test_same_fact_lost_in_both_repeats_qualifies(self):
        evidence = validate_challenges(self.baseline(), ["speech_5dB"], 2)
        self.assertEqual(len(evidence), 4)
        self.assertEqual(evidence.text_id.nunique(), 2)

    def test_unrelated_failures_across_repeats_do_not_qualify(self):
        frame = self.baseline()
        mask = (frame.condition != "clean") & ((frame.text_id == "A") == (frame.replicate == 0))
        for i in frame[mask].index:
            frame.at[i, "fact_details"] = {"code": {"recovered": True}}
        with self.assertRaisesRegex(ValueError, "two texts"):
            validate_challenges(frame, ["speech_5dB"], 2)

    def test_clean_failures_cannot_be_attributed_to_noise(self):
        frame = self.baseline()
        for i in frame[frame.condition == "clean"].index:
            frame.at[i, "fact_details"] = {"code": {"recovered": False}}
        with self.assertRaisesRegex(ValueError, "matched clean"):
            validate_challenges(frame, ["speech_5dB"], 2)

    def test_missing_repeat_and_duplicate_rows_are_rejected(self):
        frame = self.baseline()
        with self.assertRaises(ValueError):
            validate_challenges(frame[frame.replicate == 0], ["speech_5dB"], 2)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_challenges(pd.concat([frame, frame.iloc[:1]]), ["speech_5dB"], 2)
        with self.assertRaises(ValueError):
            validate_challenges(frame, ["clean"], 2)


if __name__ == "__main__":
    unittest.main()
