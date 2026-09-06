import tempfile
import unittest
from pathlib import Path

import pandas as pd

from dataforge.reporting import export_baseline


class ReportingTests(unittest.TestCase):
    def test_exports_failures_and_excludes_heldout_and_variants(self):
        row = dict(split="dev", variant="baseline", clip_id="test", text_id="critical_01",
                   replicate=0, condition="speech_5dB", noise_id="speech", snr_db=5,
                   wer=0.2, fact_recovery=0.5, estoi=0.8, dnsmos_ovrl=3.4,
                   reference_text="do not cancel", transcript="cancel", audio_path="test.wav",
                   fact_details={"negation": {"recovered": False, "conflict": True}})
        frame = pd.DataFrame([row, row | {"split": "heldout"}, row | {"variant": "slow"}])
        with tempfile.TemporaryDirectory() as directory:
            summary, failures = export_baseline(frame, directory)
            self.assertEqual(summary.clips.sum(), 1)
            self.assertEqual(failures.fact_id.tolist(), ["negation"])
            self.assertTrue(failures.iloc[0].conflict)
            self.assertEqual(len(list(Path(directory).glob("baseline_*.png"))), 4)
            self.assertEqual(len(pd.read_csv(Path(directory) / "baseline_results.csv")), 1)

    def test_perfect_baseline_still_exports_readable_empty_failure_table(self):
        row = dict(split="dev", variant="baseline", clip_id="clean", text_id="general_01",
                   replicate=0, condition="clean", noise_id="clean", snr_db=None,
                   wer=0, fact_recovery=None, estoi=None, dnsmos_ovrl=4,
                   fact_details={})
        with tempfile.TemporaryDirectory() as directory:
            _, failures = export_baseline(pd.DataFrame([row]), directory)
            self.assertTrue(failures.empty)
            saved = pd.read_csv(Path(directory) / "baseline_fact_failures.csv")
            self.assertIn("fact_id", saved.columns)


if __name__ == "__main__":
    unittest.main()
