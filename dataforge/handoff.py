"""Copy measured evidence into a consuming branch checkout without changing it."""

import csv
import hashlib
import json
import shutil
from pathlib import Path


def file_hash(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def copy_once(source, target):
    source, target = Path(source), Path(target)
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"Expected a regular source file: {source}")
    if target.exists():
        if not target.is_file() or file_hash(source) != file_hash(target):
            raise ValueError(f"Different file already exists; choose a new destination: {target}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_run(source, inputs, for_delivery=False):
    """Copy baseline tables, metadata and clips; optionally copy TTS cache inputs.

    Datasets/model downloads remain in their original shared Drive locations.
    Never combines observations from different runs. Repeating a copy verifies
    existing bytes; it cannot overwrite a different artifact.
    """
    source = Path(source).resolve()
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    run_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    target = Path(inputs).resolve() / run_id[:16]
    if target == source or target.is_relative_to(source):
        raise ValueError("Copy evidence to a separate consumer input directory")
    names = ["manifest.json", "baseline_results.csv"]
    optional = ["results.csv", "evidence_scope.json", "baseline_condition_summary.csv",
                "baseline_fact_failures.csv", "noise_failure_evidence.csv", "runtime_preflight.json",
                "git-revision.txt", "pip-freeze.txt", "ffmpeg-version.txt", "catalog_check.json"]
    names += [name for name in optional if (source / name).is_file()]
    names += [p.name for p in source.glob("baseline_*.png")]
    plan = [(source / name, Path(name)) for name in names]
    plan += [(p, Path("clips") / p.name) for p in (source / "clips").glob("*.wav")]
    with (source / "baseline_results.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or any(r.get("run_id") != run_id or r.get("split") != "dev" or
                       r.get("variant") != "baseline" for r in rows):
        raise ValueError("Expected development baseline rows from this manifest")
    remap = {str(source).replace("\\", "/"): str(target).replace("\\", "/")}
    for row in rows:
        original = row["audio_path"].replace("\\", "/")
        if "/clips/" in original:
            remap[original.rsplit("/clips/", 1)[0]] = str(target).replace("\\", "/")
    if for_delivery:
        records = []
        for path in (source / "rows").glob("*.json"):
            row = json.loads(path.read_text(encoding="utf-8"))
            if row.get("split") == "dev" and row.get("variant") == "baseline":
                records.append(row)
                plan.append((path, Path("rows") / path.name))
        if {r["clip_id"] for r in records} != {r["clip_id"] for r in rows}:
            raise ValueError("Delivery needs the baseline rows/ JSON records as well as its CSV")
        cache = Path(json.loads((source / "synthesis_cache.json").read_text())["path"])
        for name in sorted({Path(r["source_audio"]).name for r in records}):
            plan += [(cache / name, Path("synthesis") / name),
                     ((cache / name).with_suffix(".json"), (Path("synthesis") / name).with_suffix(".json"))]
        plan.append((cache / "request_ledger.json", Path("synthesis/request_ledger.json")))
    hashes = {str(relative).replace("\\", "/"): file_hash(path) for path, relative in plan}
    record = {"run_id": run_id, "source_directory": str(source), "for_delivery": for_delivery,
              "audio_path_remap": remap, "files": hashes}
    receipt = target / "handoff.json"
    if receipt.exists() and json.loads(receipt.read_text()) != record:
        raise ValueError("The source changed after the previous copy; choose a new consumer inputs directory")
    for path, relative in plan:
        copy_once(path, target / relative)
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return target


def copy_grid_results(source, inputs, expected_run_id):
    """Copy optional grid conclusions into the A/B branch for human review."""
    source = Path(source).resolve()
    record = json.loads((source / "analysis_record.json").read_text())
    if record["run_id"] != expected_run_id or record["settings"]["split"] != "dev" or record["settings"]["variant"] != "baseline":
        raise ValueError("Use grid results for this development baseline")
    target = Path(inputs) / file_hash(source / "analysis_record.json")[:16]
    for name in ("analysis_record.json", "development_challenge_cases.csv", "breakpoint_intervals.csv", "REPORT.md"):
        copy_once(source / name, target / name)
    return target


def verify_handoff(directory):
    directory = Path(directory).resolve()
    record = json.loads((directory / "handoff.json").read_text())
    for relative, expected in record["files"].items():
        path = (directory / relative).resolve()
        if not path.is_relative_to(directory) or file_hash(path) != expected:
            raise ValueError("Copied evidence changed or escaped its input directory")
    return record
