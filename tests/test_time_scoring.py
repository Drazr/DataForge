import unittest
from pathlib import Path

from dataforge.experiment import canonicalize_time, fact_score


class TimeScoringTests(unittest.TestCase):
    def test_equivalent_explicit_clock_formats(self):
        facts = [{"id": "time", "aliases": ["9:20 am", "nine twenty a m"]}]
        for text in ("9.20am", "9:20 a.m.", "920 a.m.", "09:20 AM", "9-20am", "nine twenty a m"):
            with self.subTest(text=text):
                self.assertEqual(fact_score(text, facts)[0], 1)

    def test_wrong_times_and_numeric_boundaries_remain_errors(self):
        facts = [{"id": "time", "aliases": ["9:20 am"]}]
        for text in ("9.28am", "9:20 pm", "9:60am", "1920am", "9:20", "reference 920"):
            with self.subTest(text=text):
                self.assertEqual(fact_score(text, facts)[0], 0)

    def test_other_fact_types_are_not_relaxed(self):
        facts = [{"id": "name", "aliases": ["Sara Khan"]},
                 {"id": "code", "aliases": ["5482"]},
                 {"id": "time", "aliases": ["9:20 am"]}]
        score, details = fact_score("Sarah Khan, code 5418, at 9.20am", facts)
        self.assertAlmostEqual(score, 1 / 3)
        self.assertFalse(details["name"]["recovered"])
        self.assertFalse(details["code"]["recovered"])

    def test_time_conflicts_use_the_same_normalization(self):
        facts = [{"id": "time", "aliases": ["9:20 am"], "forbidden": ["9:28 am"]}]
        self.assertEqual(fact_score("9.20am or 928 a.m.", facts)[0], 0)

    def test_v2_notebook_uses_the_shared_experiment_scorer(self):
        source = Path(__file__).resolve().parents[1] / "colab_noise_masking.py"
        notebook = source.read_text()
        self.assertIn("from dataforge.experiment import Experiment", notebook)
        self.assertNotIn("def canonicalize_time", notebook)
        self.assertIs(canonicalize_time, fact_score.__globals__["canonicalize_time"])
