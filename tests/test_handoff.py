import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from dataforge.handoff import copy_run, copy_grid_results, verify_handoff


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "producer"
        self.source.mkdir()
        manifest = {"config": {"replicates": 2}}
        self.run_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        (self.source / "manifest.json").write_text(json.dumps(manifest))
        row = {"run_id": self.run_id, "split": "dev", "variant": "baseline", "clip_id": "a",
               "audio_path": "/original/run/clips/a.wav"}
        with (self.source / "baseline_results.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=row)
            writer.writeheader()
            writer.writerow(row)
        (self.source / "clips").mkdir()
        (self.source / "clips/a.wav").write_bytes(b"synthetic test bytes")

    def test_copy_is_independent_verified_and_repeatable(self):
        copied = copy_run(self.source, self.root / "consumer/inputs")
        self.assertEqual(copy_run(self.source, self.root / "consumer/inputs"), copied)
        receipt = verify_handoff(copied)
        self.assertEqual(receipt["run_id"], self.run_id)
        self.assertEqual(receipt["audio_path_remap"]["/original/run"], str(copied).replace("\\", "/"))
        self.assertTrue((copied / "clips/a.wav").is_file())
        (copied / "baseline_results.csv").write_text("tampered")
        with self.assertRaises(ValueError):
            verify_handoff(copied)
        with self.assertRaises(ValueError):
            copy_run(self.source, self.root / "consumer/inputs")

    def test_delivery_requires_scored_json_rows(self):
        with self.assertRaisesRegex(ValueError, "JSON records"):
            copy_run(self.source, self.root / "consumer/inputs", for_delivery=True)

    def test_grid_copy_rejects_unrelated_or_heldout_evidence(self):
        source = self.root / "grid"
        source.mkdir()
        record = {"run_id": self.run_id, "settings": {"split": "dev", "variant": "baseline"}}
        (source / "analysis_record.json").write_text(json.dumps(record))
        for name in ("development_challenge_cases.csv", "breakpoint_intervals.csv", "REPORT.md"):
            (source / name).write_text("synthetic")
        copied = copy_grid_results(source, self.root / "delivery/inputs/grid", self.run_id)
        self.assertTrue((copied / "development_challenge_cases.csv").is_file())
        with self.assertRaises(ValueError):
            copy_grid_results(source, self.root / "delivery/inputs/grid", "wrong")
        record["settings"]["split"] = "heldout"
        (source / "analysis_record.json").write_text(json.dumps(record))
        with self.assertRaises(ValueError):
            copy_grid_results(source, self.root / "delivery/inputs/grid", self.run_id)


if __name__ == "__main__":
    unittest.main()
