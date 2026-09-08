"""Check that the supplied evidence still agrees with the consumer's scorer."""
import hashlib
import json
from pathlib import Path
import unittest

import pandas as pd
from dataforge.experiment import fact_score, validate_challenges

ROOT = Path(__file__).resolve().parents[1]


class StressEvidenceTests(unittest.TestCase):
    def test_producer_scores_and_challenge_match_consumer(self):
        evidence = ROOT / "inputs/noise_masking_review/6bd1eb398398af0e"
        manifest = json.loads((evidence / "manifest.json").read_text())
        rows = json.loads((evidence / "baseline_rows.json").read_text())
        run_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        implementation = (ROOT / "dataforge/experiment.py").read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(implementation).hexdigest(), manifest["implementation_sha256"])
        self.assertEqual(len(rows), 210)
        self.assertEqual({row["run_id"] for row in rows}, {run_id})
        facts = {item["id"]: item["facts"] for item in manifest["corpus"]}
        for row in rows:
            self.assertEqual(row["split"], "dev")
            score, details = fact_score(row["transcript"], facts[row["text_id"]])
            self.assertEqual(score, row["fact_recovery"])
            self.assertEqual(details, row["fact_details"])
        recurrent = validate_challenges(pd.DataFrame(rows), ["competing_speech_-5dB"], 2)
        self.assertEqual(set(recurrent.text_id), {"critical_01", "critical_03", "critical_05"})
