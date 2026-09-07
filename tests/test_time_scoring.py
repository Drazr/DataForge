import ast
import re
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

    def test_standalone_review_uses_identical_time_normalization(self):
        source = Path(__file__).resolve().parents[1] / "colab_noise_masking.py"
        if not source.exists():
            self.skipTest("Standalone review belongs to the Noise-Masking branch")
        tree = ast.parse(source.read_text())
        helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                      and node.name == "canonicalize_time")
        namespace = {"re": re}
        exec(compile(ast.Module(body=[helper], type_ignores=[]), "cell10", "exec"), namespace)
        for text in ("9.20am", "920 a.m.", "9.28am", "11.60am", "1-25pm", "1920am"):
            self.assertEqual(namespace["canonicalize_time"](text), canonicalize_time(text))
