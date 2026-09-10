"""Synthetic producer-contract fixtures; these are not measured Rime results."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from dataforge.grid_analysis import (interval_analysis, load_evidence, load_performance_grid, remap_audio,
                                     run_analysis, validate_settings, write_json)


ROOT = Path(__file__).resolve().parents[1]


def fixture(directory, repeats=2):
    settings = json.loads((ROOT / "grid_analysis.json").read_text())
    settings["bootstrap_samples"] = 100
    config = {"model_id": "coda", "speaker": "celeste", "endpoint": "fixture-only",
              "phone_sample_rate": 8000, "snrs_db": [10, 5, 0], "replicates": repeats}
    corpus = [{"id": f"text_{i}", "split": "dev", "facts": [{"id": "code"}] if i < 3 else []}
              for i in range(4)]
    noises = [{"id": name, "path": f"/synthetic/{name}.wav", "sha256": name * 8,
               "offset_s": 0, "reference_rms": 0.1, "kind": name}
              for name in ("speech", "traffic")]
    manifest = {"config": config, "corpus": corpus, "noise": noises, "speech_level_method": "fixture"}
    run_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    scope = {"synthesis_repeats": repeats, "snrs_db": [10, 5, 0], "noise_sources": 2,
             "texts_by_split": {"dev": 4}, "critical_texts_by_split": {"dev": 3}}
    rows, evidence, failures = [], [], []
    for item in corpus:
        for rep in range(repeats):
            clean_id = f"{item['id']}_r{rep}_clean"
            for noise, snr in [(None, None)] + [(n, s) for n in noises for s in (10, 5, 0)]:
                condition = "clean" if noise is None else f"{noise['id']}_{snr}dB"
                clip_id = f"{item['id']}_r{rep}_{condition}"
                wer = {None: 0.0, 10: 0.05, 5: 0.4, 0: 0.6}[snr]
                recovery = float(snr in (None, 10)) if item["facts"] else None
                row = dict(run_id=run_id, split="dev", variant="baseline", clip_id=clip_id,
                           text_id=item["id"], replicate=rep, condition=condition,
                           noise_id=noise["id"] if noise else "clean", snr_db=snr,
                           measured_snr_db=snr - 0.2 if snr is not None else None,
                           noise_file=noise["path"] if noise else None,
                           noise_sha256=noise["sha256"] if noise else None,
                           noise_offset_s=0 if noise else None, noise_kind=noise["kind"] if noise else "clean",
                           noise_reference_rms=0.1 if noise else None, sample_rate=8000,
                           model_id="coda", speaker="celeste", endpoint="fixture-only",
                           speech_level_method="fixture", transport="HTTP WAV -> local PCMU roundtrip",
                           noise_placement="after simulated phone codec", source_audio=f"/{item['id']}_r{rep}.wav",
                           duration_s=3.0, fact_count=len(item["facts"]), wer=wer, fact_recovery=recovery,
                           estoi={None: None, 10: 0.9, 5: 0.6, 0: 0.4}[snr],
                           audio_path=f"/synthetic/{clip_id}.wav", dnsmos_ovrl=3.0,
                           reference_text="code one", transcript="code one" if recovery else "code two")
                rows.append(row)
                if recovery == 0:
                    failures.append({k: row[k] for k in ["clip_id", "text_id", "replicate", "condition",
                                                        "reference_text", "transcript", "audio_path"]}
                                    | {"fact_id": "code", "conflict": True})
                    evidence.append(dict(text_id=item["id"], replicate=rep, condition=condition, fact_id="code",
                                         clean_clip_id=clean_id, noisy_clip_id=clip_id,
                                         clean_audio_path=f"/synthetic/{clean_id}.wav", audio_path=row["audio_path"]))
    frame = pd.DataFrame(rows)
    frame.to_csv(directory / "baseline_results.csv", index=False)
    pd.DataFrame(evidence).to_csv(directory / "noise_failure_evidence.csv", index=False)
    pd.DataFrame(failures).to_csv(directory / "baseline_fact_failures.csv", index=False)
    write_json(directory / "manifest.json", manifest)
    write_json(directory / "evidence_scope.json", scope)
    return settings, frame, manifest


class GridAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.settings, self.frame, self.manifest = fixture(self.path)

    def save_frame(self):
        self.frame.to_csv(self.path / "baseline_results.csv", index=False)

    def analyze(self):
        frame, manifest, _, missing, _ = load_evidence(self.path, self.settings)
        intervals, pairs = interval_analysis(frame, manifest, self.settings)
        return intervals, pairs, missing

    def use_v2_contract(self):
        self.manifest["config"]["mixing_protocol"] = "window_rms_no_wrap_v2"
        run_id = hashlib.sha256(json.dumps(self.manifest, sort_keys=True).encode()).hexdigest()
        self.frame["run_id"] = run_id
        self.frame["mixing_protocol"] = "window_rms_no_wrap_v2"
        noisy = self.frame.condition != "clean"
        self.frame.loc[noisy, "measured_snr_db"] = self.frame.loc[noisy, "snr_db"]
        self.frame["noise_window_rms"] = np.where(noisy, 0.1, np.nan)
        self.frame["noise_gain"] = np.where(noisy, 0.2, np.nan)
        self.frame["noise_looped"] = False
        self.frame["source_audio_sha256"] = self.frame.source_audio.map(
            lambda value: hashlib.sha256(value.encode()).hexdigest()
        )
        write_json(self.path / "manifest.json", self.manifest)
        self.save_frame()

    def limits(self):
        self.settings["acceptance"] = dict(maximum_wer=0.2, minimum_fact_recovery=0.9,
                                          rationale="Synthetic test limits", established_before_review=True)
        self.settings["repeatability"].update(minimum_texts=2, minimum_text_fraction=0.5)

    def test_end_to_end_export_retains_dnsmos_as_supporting_metric(self):
        result = run_analysis(self.path, self.settings, self.path / "analysis")
        self.assertEqual(len(result["intervals"]), 12)
        self.assertTrue(result["intervals"].repeatable_deterioration.any())
        self.assertFalse(result["intervals"].supported_breakpoint.any())
        self.assertFalse(result["challenges"].empty)
        selected = pd.read_csv(self.path / "analysis/selected_observations.csv")
        self.assertIn("dnsmos_ovrl", selected)
        self.assertNotIn("dnsmos_ovrl", set(result["intervals"].metric))
        self.assertEqual(len(list((self.path / "analysis").glob("adjacent_*.png"))), 3)
        self.assertEqual(result["report"]["missing_rows"], 0)
        self.assertTrue(selected.loc[selected.fact_count == 0, "fact_recovery"].isna().all())
        with self.assertRaises(FileExistsError):
            run_analysis(self.path, self.settings, self.path / "analysis")

    def test_limits_find_crossing_not_already_failed_interval(self):
        self.limits()
        intervals, _, _ = self.analyze()
        primary = intervals[intervals.metric != "estoi"]
        self.assertTrue(primary[primary.higher_snr_db == 10].supported_breakpoint.all())
        lower = primary[primary.higher_snr_db == 5]
        self.assertFalse(lower.supported_breakpoint.any())
        self.assertEqual(set(lower.acceptance_status), {"already_unacceptable_at_higher_snr"})

    def test_equality_at_limit_is_acceptable(self):
        self.limits()
        self.settings["acceptance"]["maximum_wer"] = 0.4
        intervals, _, _ = self.analyze()
        wer = intervals[intervals.metric == "wer"]
        self.assertEqual(set(wer[wer.higher_snr_db == 10].acceptance_status), {"both_acceptable"})
        self.assertTrue(wer[wer.higher_snr_db == 5].supported_breakpoint.all())

    def test_missing_middle_level_does_not_bridge(self):
        self.frame = self.frame[self.frame.condition != "speech_5dB"]
        self.save_frame()
        self.limits()
        intervals, pairs, missing = self.analyze()
        self.assertEqual(len(missing), 8)
        speech = intervals[intervals.noise_id == "speech"]
        self.assertFalse(speech.complete_grid_pair.any())
        self.assertFalse(speech.supported_breakpoint.any())
        self.assertFalse(((pairs.higher_snr_db == 10) & (pairs.lower_snr_db == 0)).any())

    def test_duplicate_rows_rejected(self):
        self.frame = pd.concat([self.frame, self.frame.iloc[:1]], ignore_index=True)
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.analyze()

    def test_manifest_mismatch_rejected(self):
        self.frame.loc[0, "run_id"] = "other-run"
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.analyze()

    def test_scope_mismatch_rejected(self):
        scope = json.loads((self.path / "evidence_scope.json").read_text())
        scope["synthesis_repeats"] = 8
        write_json(self.path / "evidence_scope.json", scope)
        with self.assertRaisesRegex(ValueError, "scope"):
            self.analyze()

    def test_baseline_without_ab_winner_or_scope_file(self):
        (self.path / "evidence_scope.json").unlink()
        self.assertFalse((self.path / "results.csv").exists())
        self.assertFalse((self.path / "selection.json").exists())
        result = run_analysis(self.path, self.settings, self.path / "baseline-only")
        self.assertEqual(result["report"]["scope_source"], "derived from manifest.json")
        self.assertEqual(result["report"]["missing_rows"], 0)
        self.assertEqual(result["report"]["evidence_scope"]["texts_by_split"], {"dev": 4})
        self.assertNotIn("evidence_scope.json", result["report"]["source_hashes"])

    def producer_summary(self):
        summary = self.frame.groupby(["condition", "noise_id", "snr_db"], dropna=False).agg(
            clips=("clip_id", "count"), texts=("text_id", "nunique"),
            critical_clips=("fact_recovery", "count"), wer=("wer", "mean"),
            fact_recovery=("fact_recovery", "mean"), estoi=("estoi", "mean"),
            dnsmos_ovrl=("dnsmos_ovrl", "mean"),
        ).reset_index()
        summary.to_csv(self.path / "baseline_condition_summary.csv", index=False)
        return summary

    def test_existing_summary_is_reused_and_retains_dnsmos(self):
        self.producer_summary()
        result = run_analysis(self.path, self.settings, self.path / "reused-grid")
        self.assertEqual(result["report"]["grid_source"], "baseline_condition_summary.csv")
        self.assertIn("dnsmos_ovrl", result["grid"])
        self.assertIn("measured_snr_db_min", result["grid"])
        self.assertIn("baseline_condition_summary.csv", result["report"]["source_hashes"])

    def test_stale_summary_falls_back_to_selected_rows(self):
        summary = self.producer_summary()
        summary["wer"] = 42
        summary.to_csv(self.path / "baseline_condition_summary.csv", index=False)
        warnings = []
        grid, source = load_performance_grid(self.path, self.frame, self.settings, warnings)
        self.assertEqual(source, "derived from selected observations")
        self.assertLess(grid.wer.max(), 1)
        self.assertTrue(any("wer differs" in w for w in warnings))

    def test_baseline_summary_is_not_reused_for_intervention(self):
        self.producer_summary()
        self.settings.update(input_file="results.csv", variant="slow")
        extra = self.frame.copy()
        extra["variant"], extra["wer"] = "slow", 0
        grid, source = load_performance_grid(self.path, extra, self.settings, [])
        self.assertEqual(source, "derived from selected observations")
        self.assertEqual(grid.wer.sum(), 0)

    def test_missing_baseline_explains_export_stage(self):
        self.frame.to_csv(self.path / "results.csv", index=False)
        (self.path / "baseline_results.csv").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "Cell 10"):
            load_evidence(self.path, self.settings)

    def test_noise_source_and_speech_control_mismatch_rejected(self):
        self.frame.loc[self.frame.condition == "speech_5dB", "noise_offset_s"] = 3
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "Noise control"):
            self.analyze()
        self.frame.loc[self.frame.condition == "speech_5dB", "noise_offset_s"] = 0
        self.frame.loc[0, "source_audio"] = "/different.wav"
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "Speech source"):
            self.analyze()

    def test_v2_contract_rejects_looping_snr_drift_and_changed_windows(self):
        self.use_v2_contract()
        self.analyze()
        noisy_index = self.frame.index[self.frame.condition != "clean"][0]
        self.frame.loc[noisy_index, "noise_looped"] = True
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "never loop"):
            self.analyze()
        self.frame.loc[noisy_index, "noise_looped"] = False
        self.frame.loc[noisy_index, "measured_snr_db"] += 0.5
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "differs"):
            self.analyze()
        self.frame.loc[noisy_index, "measured_snr_db"] -= 0.5
        self.frame.loc[noisy_index, "noise_window_rms"] = 0.2
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "window changed"):
            self.analyze()

    def test_partial_results_selection_does_not_pool_variants(self):
        extra = self.frame.copy()
        extra["variant"] = "slow"
        extra["wer"] = 0
        pd.concat([self.frame, extra]).to_csv(self.path / "results.csv", index=False)
        self.settings["input_file"] = "results.csv"
        frame, _, _, _, _ = load_evidence(self.path, self.settings)
        self.assertEqual(len(frame), len(self.frame))
        self.settings["variant"] = "slow"
        result = run_analysis(self.path, self.settings, self.path / "slow")
        self.assertTrue(result["challenges"].empty)
        self.assertEqual(result["grid"].wer.sum(), 0)

    def test_repeats_are_not_independent_texts(self):
        intervals, _, _ = self.analyze()
        self.assertEqual(set(intervals[intervals.metric == "fact_recovery"].complete_texts), {3})
        self.assertEqual(set(intervals[intervals.metric == "wer"].complete_texts), {4})
        # Duplicate synthesis realizations add no texts or artificial CI precision.
        other = self.path / "more_repeats"
        other.mkdir()
        settings, _, _ = fixture(other, repeats=4)
        frame, manifest, _, _, _ = load_evidence(other, settings)
        more, _ = interval_analysis(frame, manifest, settings)
        np.testing.assert_allclose(intervals.ci95_low, more.ci95_low)
        np.testing.assert_allclose(intervals.ci95_high, more.ci95_high)

    def test_heldout_reports_without_selecting_challenges(self):
        for item in self.manifest["corpus"]:
            item["split"] = "heldout"
        self.frame["split"] = "heldout"
        self.frame["run_id"] = hashlib.sha256(json.dumps(self.manifest, sort_keys=True).encode()).hexdigest()
        write_json(self.path / "manifest.json", self.manifest)
        scope = json.loads((self.path / "evidence_scope.json").read_text())
        scope["texts_by_split"], scope["critical_texts_by_split"] = {"heldout": 4}, {"heldout": 3}
        write_json(self.path / "evidence_scope.json", scope)
        self.frame.to_csv(self.path / "results.csv", index=False)
        self.settings.update(input_file="results.csv", split="heldout")
        result = run_analysis(self.path, self.settings, self.path / "heldout")
        self.assertEqual(result["report"]["selected_rows"], len(self.frame))
        self.assertTrue(result["challenges"].empty)

    def test_matched_delta_sign_and_text_averaging(self):
        mask = (self.frame.condition == "speech_5dB") & (self.frame.text_id == "text_0")
        self.frame.loc[mask & (self.frame.replicate == 0), "wer"] = 0.6
        self.frame.loc[mask & (self.frame.replicate == 1), "wer"] = 0.8
        self.save_frame()
        intervals, pairs, _ = self.analyze()
        row = intervals[(intervals.noise_id == "speech") & (intervals.higher_snr_db == 10) & (intervals.metric == "wer")].iloc[0]
        self.assertAlmostEqual(row.mean_deterioration, (0.65 + 3 * 0.35) / 4)
        self.assertLess(row.ci95_low, row.ci95_high)
        self.assertTrue((pairs.fact_recovery_deterioration.dropna() >= 0).all())

    def test_one_repeat_cannot_support_repeatability(self):
        other = self.path / "one_repeat"
        other.mkdir()
        settings, _, _ = fixture(other, repeats=1)
        frame, manifest, _, _, _ = load_evidence(other, settings)
        intervals, _ = interval_analysis(frame, manifest, settings)
        self.assertFalse(intervals.repeatable_deterioration.any())

    def test_inconsistent_repeats_do_not_support_crossing(self):
        self.limits()
        mask = (self.frame.condition == "speech_5dB") & (self.frame.replicate == 1)
        self.frame.loc[mask, "wer"] = 0.01
        self.save_frame()
        intervals, _, _ = self.analyze()
        row = intervals[(intervals.noise_id == "speech") & (intervals.higher_snr_db == 10) & (intervals.metric == "wer")].iloc[0]
        self.assertFalse(row.repeatable_deterioration)
        self.assertFalse(row.supported_breakpoint)
        self.assertEqual(row.crossing_texts, 0)

    def test_undefined_values_not_zero_filled(self):
        self.frame.loc[0, "estoi"] = 0
        self.save_frame()
        with self.assertRaisesRegex(ValueError, "Clean reference"):
            self.analyze()

    def test_limits_require_rationale_and_prior_choice(self):
        self.settings["acceptance"]["maximum_wer"] = 0.2
        self.settings["acceptance"]["rationale"] = ""
        self.settings["acceptance"]["established_before_review"] = False
        with self.assertRaisesRegex(ValueError, "rationale"):
            validate_settings(self.settings)

    def test_missing_optional_evidence_keeps_analysis_available(self):
        (self.path / "noise_failure_evidence.csv").unlink()
        result = run_analysis(self.path, self.settings, self.path / "without_links")
        self.assertTrue(result["challenges"].empty)
        self.assertTrue(any("Missing fact" in w for w in result["report"]["warnings"]))

    def test_stale_evidence_rejected(self):
        evidence = pd.read_csv(self.path / "noise_failure_evidence.csv")
        evidence.loc[0, "noisy_clip_id"] = "unrelated"
        evidence.to_csv(self.path / "noise_failure_evidence.csv", index=False)
        with self.assertRaisesRegex(ValueError, "outside"):
            run_analysis(self.path, self.settings, self.path / "stale")

    def test_path_remapping_respects_directory_boundaries(self):
        mapping = {"/old/run": "/new/run"}
        self.assertEqual(remap_audio("/old/run/clips/a.wav", mapping), "/new/run/clips/a.wav")
        self.assertEqual(remap_audio("/old/runner/a.wav", mapping), "/old/runner/a.wav")

    def test_colab_cells_compile_and_have_three_blank_line_gaps(self):
        source = (ROOT / "colab_grid_analysis.py").read_text()
        self.assertEqual(source.count("# %% Cell"), 7)
        self.assertEqual(source.count("\n\n\n\n# %% Cell"), 6)
        for index, cell in enumerate(source.split("\n\n\n\n# %% Cell")):
            compile(cell if index == 0 else "# %% Cell" + cell, f"cell_{index + 1}", "exec")


if __name__ == "__main__":
    unittest.main()
