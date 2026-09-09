import copy
import ast
import importlib.util
import io
import json
import re
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("review_audio", ROOT / "scripts/review_development_audio.py")
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class NotebookSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load only the pure helpers, without executing Colab or loading a GPU model.
        tree = ast.parse((ROOT / "colab_noise_ab.py").read_text())
        helpers = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name in {"parse_review", "invalid_review_fields", "request_valid_review"}]
        cls.scope = {"json": json, "re": re, "REVIEW_PROMPT": "full schema"}
        exec(compile(ast.Module(body=helpers, type_ignores=[]), "notebook_helpers", "exec"), cls.scope)

    def test_reported_schema_failure_retried_without_inventing_fields(self):
        bad = {"transcript": "Audible speech", "competing_voice": False, "artifact": False,
               "naturalness": "acceptable", "notes": "Clear"}
        good = {"transcript": "Audible speech", "competing_voice": False, "artifacts": "uncertain",
                "clarity": "partial", "naturalness": "uncertain", "notes": "Unsure"}
        corrections = []
        def generate(correction):
            corrections.append(correction)
            return json.dumps(bad if len(corrections) == 1 else good)
        record = {}
        result = self.scope["request_valid_review"](generate, record)
        self.assertEqual(result, good)
        self.assertEqual(len(record["generation_attempts"]), 2)
        self.assertIn("clarity", corrections[1])
        self.assertIn("artifact", corrections[1])

    def test_persistent_missing_field_uses_focused_audio_judgment(self):
        incomplete = {"transcript": "Audible speech", "clarity": "acceptable",
                      "competing_voice": False, "naturalness": "acceptable", "notes": "Clear"}
        instructions = []
        def generate(instruction):
            instructions.append(instruction)
            return json.dumps(incomplete if len(instructions) < 3 else
                              {"artifacts": "none", "clarity": "clear"})
        record = {}
        result = self.scope["request_valid_review"](generate, record)
        self.assertEqual(result["artifacts"], "none")
        self.assertEqual(len(record["generation_attempts"]), 3)
        self.assertEqual(record["generation_attempts"][2]["requested_fields"], ["artifacts", "clarity"])
        self.assertIn("only the missing", instructions[2])

    def test_invalid_focused_response_stops_after_three_attempts(self):
        record = {}
        with self.assertRaises(ValueError):
            self.scope["request_valid_review"](lambda _: '{"transcript":"speech"}', record)
        self.assertEqual(len(record["generation_attempts"]), 3)

    def test_fenced_valid_json_accepted_and_nonobject_rejected(self):
        good = {"transcript": "speech", "clarity": "clear", "competing_voice": False,
                "artifacts": "none", "naturalness": "acceptable", "notes": ""}
        self.assertEqual(self.scope["parse_review"]("```json\n" + json.dumps(good) + "\n```"), good)
        with self.assertRaises(ValueError):
            self.scope["parse_review"]("[]")


class ModelReviewTests(unittest.TestCase):
    def record(self, **overrides):
        row = {"status": "ok", "variant": "repeat", "condition": "clean", "fact_recovery": 1.0,
               "judgment": {"naturalness": "acceptable", "artifacts": "none"}}
        row.update(overrides)
        return row

    def test_missing_reviews_never_pass(self):
        self.assertFalse(review.summarize([self.record()], 56)["model_gate_pass"])

    def test_uncertain_naturalness_fails_closed(self):
        row = self.record(judgment={"naturalness": "uncertain", "artifacts": "none"})
        self.assertFalse(review.summarize([row], 1)["model_gate_pass"])

    def test_missing_fact_fails_even_when_natural(self):
        result = review.summarize([self.record(fact_recovery=6 / 7)], 1)
        self.assertFalse(result["listening_review"]["repeat"]["facts_preserved"])
        self.assertTrue(result["listening_review"]["repeat"]["quality_acceptable"])

    def test_model_pass_never_becomes_human_review(self):
        result = review.summarize([self.record()], 1)
        self.assertTrue(result["model_gate_pass"])
        self.assertEqual(result["human_review"], "pending")
        self.assertEqual(result["listening_review"]["repeat"]["reviewer_type"], "model")

    def test_truncated_or_wrong_type_response_rejected(self):
        judgment = {"transcript": "Hello", "clarity": "clear", "competing_voice": False,
                    "artifacts": "none", "naturalness": "acceptable", "notes": ""}
        response = {"choices": [{"finish_reason": "length", "message": {"content": json.dumps(judgment)}}]}
        with self.assertRaises(ValueError):
            review.parse_judgment(response)
        response["choices"][0]["finish_reason"] = "stop"
        judgment["competing_voice"] = "false"
        response["choices"][0]["message"]["content"] = json.dumps(judgment)
        with self.assertRaises(ValueError):
            review.parse_judgment(response)

    def test_archive_traversal_rejected_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../escape.txt", "bad")
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                review.load_bundle(path, {})

    def test_prompt_withholds_answer_and_existing_transcript(self):
        self.assertNotIn("Mira Patel", review.PROMPT)
        self.assertNotIn("7294", review.PROMPT)
        self.assertIn("instead of guessing", review.PROMPT)


if __name__ == "__main__":
    unittest.main()
