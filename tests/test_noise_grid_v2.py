import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from dataforge.noise_grid_v2 import SELECTION_BASIS, select_noise_panel


class NoiseGridV2PanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        rng = np.random.default_rng(20260910)
        for family in ("speech", "noise"):
            directory = self.root / family / "set"
            directory.mkdir(parents=True)
            for index in range(3):
                audio = rng.normal(0, 0.03 + index * 0.002, 20000).astype(np.float32)
                sf.write(directory / f"{index}.wav", audio, 8000, subtype="FLOAT")

    def test_panel_is_deterministic_complete_and_has_two_windows(self):
        first, audit = select_noise_panel(self.root, seed=9, minimum_window_seconds=1.0)
        second, _ = select_noise_panel(self.root, seed=9, minimum_window_seconds=1.0)
        self.assertEqual(first, second)
        self.assertEqual([row["id"] for row in first],
                         ["speech_1", "speech_2", "environment_1", "environment_2"])
        self.assertEqual(len({row["sha256"] for row in first}), 4)
        self.assertTrue(all(row["offset_b_s"] >= row["minimum_window_s"] for row in first))
        self.assertTrue(all(row["selection_basis"] == SELECTION_BASIS for row in first))
        self.assertEqual(audit["selection_basis"], SELECTION_BASIS)

    def test_pilot_hashes_are_excluded_before_scoring(self):
        original, _ = select_noise_panel(self.root, seed=11, minimum_window_seconds=1.0)
        excluded = original[0]["sha256"]
        replacement, audit = select_noise_panel(
            self.root, seed=11, excluded_hashes=[excluded], minimum_window_seconds=1.0
        )
        self.assertNotIn(excluded, {row["sha256"] for row in replacement})
        self.assertIn(excluded, audit["excluded_hashes"])
        self.assertTrue(any(row["reason"] == "used by pilot baseline"
                            for row in audit["rejected_before_completion"]))

    def test_short_sources_cannot_enter_the_panel(self):
        short = self.root / "speech" / "set" / "short.wav"
        sf.write(short, np.ones(4000, dtype=np.float32) * 0.01, 8000, subtype="FLOAT")
        panel, _ = select_noise_panel(self.root, seed=5, minimum_window_seconds=1.0)
        self.assertNotIn(short.resolve(), {Path(row["path"]).resolve() for row in panel})


if __name__ == "__main__":
    unittest.main()
