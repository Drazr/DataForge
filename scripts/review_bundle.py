"""Run Cell 10 offline against an exported review ZIP with Colab UI stubbed.

Usage: python scripts/review_bundle.py PATH_TO_ZIP
Writes docs/BASELINE_REVIEW_RESULT.json; performs no synthesis, ASR or networking.
"""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dataforge import experiment


def review_bundle(bundle_path):
    fixed_score = experiment.fact_score
    # Emulate the previous match behavior so Cell 10 is checked in a stale session.
    old_source = (ROOT / "dataforge/experiment.py").read_text().replace(
        "contains(match_text, match_phrase(alias))", "contains(transcript, alias)"
    ).replace("contains(match_text, match_phrase(phrase))", "contains(transcript, phrase)")
    tree = ast.parse(old_source)
    namespace = {"re": re}
    names = {"normalize", "contains", "fact_score", "canonicalize_time"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "old_matching", "exec"), namespace)
    experiment.fact_score = namespace["fact_score"]
    for module in ("google", "google.colab", "IPython", "IPython.display"):
        sys.modules[module] = types.ModuleType(module)
    sys.modules["google.colab"].files = types.SimpleNamespace(download=lambda path: None)
    sys.modules["IPython.display"].display = lambda *args, **kwargs: None
    sys.modules["IPython.display"].Audio = lambda *args, **kwargs: None
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        source = base / "source"
        source.mkdir()
        (source / "rows").mkdir()
        (source / "clips").mkdir()
        with zipfile.ZipFile(bundle_path) as bundle:
            rows = json.loads(bundle.read("baseline_rows.json"))
            for name in ("manifest.json", "baseline_results.csv", "baseline_condition_summary.csv",
                         "baseline_fact_failures.csv", "evidence_scope.json", "runtime_preflight.json",
                         "git-revision.txt", "pip-freeze.txt"):
                if name in bundle.namelist():
                    (source / name).write_bytes(bundle.read(name))
            for row in rows:
                clip_id = row["clip_id"]
                if Path(clip_id).name != clip_id or "/" in clip_id or "\\" in clip_id:
                    raise ValueError("Unsafe clip identifier")
                (source / "rows" / (clip_id + ".json")).write_text(json.dumps(row))
                name = "clips/" + clip_id + ".wav"
                if name in bundle.namelist():
                    (source / name).write_bytes(bundle.read(name))
        def hashes():
            return {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in source.rglob("*") if p.is_file()}
        before = hashes()
        cell = "# %% Cell 10" + (ROOT / "colab_noise_masking.py").read_text().split("# %% Cell 10", 1)[1]
        env = {"BASELINE_REVIEW_SOURCE": str(source), "BASELINE_REVIEW_EXPORT_DIR": str(base)}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(cell, "cell10", "exec"), env)
        assert before == hashes(), "Original source modified"
        for row in env["rescored_records"]:
            score, details = fixed_score(row["transcript"], env["facts_by_text"][row["text_id"]])
            assert details == row["fact_details"] and score == row["fact_recovery"]
        report = env["review_summary"]
        report["source_zip_sha256"] = hashlib.sha256(Path(bundle_path).read_bytes()).hexdigest()
        report["original_source_unchanged_verified"] = True
        report["standalone_old_runtime_matches_updated_library"] = True
        report["conditions"] = env["rescored_frame"].groupby("condition").fact_recovery.mean().to_dict()
        report["rescored_recurrent_texts"] = env["rescored_counts"].to_dict()
        (ROOT / "docs/BASELINE_REVIEW_RESULT.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    review_bundle(sys.argv[1])
