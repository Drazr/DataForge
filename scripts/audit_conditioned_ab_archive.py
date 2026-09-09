"""Validate and summarize a completed conditioned A/B Colab archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path, PurePosixPath
from statistics import mean
from zipfile import BadZipFile, ZipFile


REQUIRED_JUDGMENT_FIELDS = {
    "transcript",
    "clarity",
    "competing_voice",
    "artifacts",
    "naturalness",
    "notes",
}
VALID_CLARITY = {"clear", "partial", "unintelligible"}
VALID_ARTIFACTS = {"none", "minor", "severe", "uncertain"}
VALID_NATURALNESS = {"acceptable", "unacceptable", "uncertain"}
CHALLENGE = "competing_speech_-5dB"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(archive: ZipFile, name: str):
    return json.loads(archive.read(name))


def fail_unless(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit(archive_path: Path) -> tuple[dict, list[dict], dict[str, bytes]]:
    try:
        archive = ZipFile(archive_path)
    except BadZipFile as error:
        raise ValueError(f"Invalid ZIP archive: {archive_path}") from error

    with archive:
        names = archive.namelist()
        unsafe = [
            name
            for name in names
            if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
        ]
        fail_unless(not unsafe, f"Unsafe archive paths: {unsafe[:3]}")
        duplicates = [name for name, count in Counter(names).items() if count > 1]
        fail_unless(not duplicates, f"Duplicate archive paths: {duplicates[:3]}")
        corrupt = archive.testzip()
        fail_unless(corrupt is None, f"CRC failure: {corrupt}")

        required = {
            "manifest.json",
            "imported_baseline.json",
            "challenge.json",
            "evidence_scope.json",
            "development_comparisons.csv",
            "development_listening_queue.csv",
            "model_review_qwen/protocol.json",
            "model_review_qwen/summary.json",
        }
        missing = sorted(required - set(names))
        fail_unless(not missing, f"Missing required files: {missing}")

        response_names = sorted(
            name
            for name in names
            if name.startswith("model_review_qwen/responses/") and name.endswith(".json")
        )
        expected_response_names = [
            f"model_review_qwen/responses/{index:04d}.json" for index in range(56)
        ]
        fail_unless(response_names == expected_response_names, "Expected responses 0000-0055")

        summary = load_json(archive, "model_review_qwen/summary.json")
        protocol = load_json(archive, "model_review_qwen/protocol.json")
        challenge = load_json(archive, "challenge.json")
        imported_baseline = load_json(archive, "imported_baseline.json")
        fail_unless(challenge.get("conditions") == [CHALLENGE], "Unexpected challenge lock")

        queue_rows = list(
            csv.DictReader(io.StringIO(archive.read("development_listening_queue.csv").decode()))
        )
        review_queue = [row for row in queue_rows if row["variant"] in {"baseline", "repeat"}]
        fail_unless(len(review_queue) == 56, "Expected 56 Baseline/Repeat review rows")

        expected_keys = {
            (f"critical_{text:02d}", variant, replicate, condition)
            for text in range(1, 8)
            for variant in ("baseline", "repeat")
            for replicate in range(2)
            for condition in ("clean", CHALLENGE)
        }
        records: list[dict] = []
        audio_hashes_verified = 0
        for index, (response_name, queue_row) in enumerate(zip(response_names, review_queue)):
            record = load_json(archive, response_name)
            fail_unless(record.get("status") == "ok", f"Response {index} is not successful")
            key = (
                record.get("text_id"),
                record.get("variant"),
                record.get("replicate"),
                record.get("condition"),
            )
            queue_key = (
                queue_row["text_id"],
                queue_row["variant"],
                int(queue_row["replicate"]),
                queue_row["condition"],
            )
            fail_unless(key == queue_key, f"Response {index} does not match its queue row")

            judgment = record.get("judgment")
            fail_unless(isinstance(judgment, dict), f"Response {index} has no judgment")
            fail_unless(
                set(judgment) == REQUIRED_JUDGMENT_FIELDS,
                f"Response {index} has invalid judgment fields",
            )
            fail_unless(judgment["clarity"] in VALID_CLARITY, f"Response {index}: clarity")
            fail_unless(
                isinstance(judgment["competing_voice"], bool),
                f"Response {index}: competing_voice",
            )
            fail_unless(judgment["artifacts"] in VALID_ARTIFACTS, f"Response {index}: artifacts")
            fail_unless(
                judgment["naturalness"] in VALID_NATURALNESS,
                f"Response {index}: naturalness",
            )
            fail_unless(
                all(isinstance(judgment[field], str) for field in ("transcript", "notes")),
                f"Response {index}: transcript/notes",
            )

            fact_details = record.get("fact_details")
            fail_unless(isinstance(fact_details, dict) and fact_details, f"Response {index}: facts")
            calculated_recovery = sum(
                bool(detail.get("recovered")) for detail in fact_details.values()
            ) / len(fact_details)
            fail_unless(
                math.isclose(record.get("fact_recovery", -1), calculated_recovery),
                f"Response {index}: fact recovery mismatch",
            )

            audio_name = f"clips/{PurePosixPath(record['audio_path']).name}"
            fail_unless(audio_name in names, f"Response {index}: missing audio")
            fail_unless(
                sha256_bytes(archive.read(audio_name)) == record.get("audio_sha256"),
                f"Response {index}: audio hash mismatch",
            )
            audio_hashes_verified += 1
            records.append(record)

        actual_keys = {
            (record["text_id"], record["variant"], record["replicate"], record["condition"])
            for record in records
        }
        fail_unless(actual_keys == expected_keys, "Review matrix is incomplete or duplicated")

        repeat = [record for record in records if record["variant"] == "repeat"]
        facts_preserved = all(record["fact_recovery"] == 1.0 for record in repeat)
        quality_acceptable = all(
            record["judgment"]["naturalness"] == "acceptable"
            and record["judgment"]["artifacts"] in {"none", "minor"}
            for record in repeat
        )
        calculated_gate = facts_preserved and quality_acceptable
        fail_unless(summary.get("expected_clips") == 56, "Summary expected_clips mismatch")
        fail_unless(summary.get("successful_clips") == 56, "Summary successful_clips mismatch")
        fail_unless(summary.get("complete") is True, "Summary is incomplete")
        fail_unless(summary.get("model_gate_pass") is calculated_gate, "Gate mismatch")
        fail_unless(summary.get("model_listening_review", {}).get("repeat", {}).get("facts_preserved") is facts_preserved, "Fact gate mismatch")
        fail_unless(summary.get("model_listening_review", {}).get("repeat", {}).get("quality_acceptable") is quality_acceptable, "Quality gate mismatch")
        for key, value in protocol.items():
            fail_unless(summary.get(key) == value, f"Summary/protocol mismatch: {key}")

        comparisons = list(
            csv.DictReader(io.StringIO(archive.read("development_comparisons.csv").decode()))
        )
        passing = [row["variant"] for row in comparisons if row["screen_pass"].lower() == "true"]
        fail_unless(passing == ["repeat"], "Repeat must be the sole metric-screen pass")

        forbidden_outputs = {
            "selection.json",
            "heldout_comparison.csv",
            "results.csv",
            "condition_summary.csv",
        }
        present_forbidden = sorted(forbidden_outputs & set(names))
        fail_unless(not present_forbidden, f"Post-selection outputs present: {present_forbidden}")

        variants = {}
        for variant in ("baseline", "repeat"):
            variant_records = [record for record in records if record["variant"] == variant]
            recoveries = [record["fact_recovery"] for record in variant_records]
            variants[variant] = {
                "clips": len(variant_records),
                "fact_recovery_mean": mean(recoveries),
                "fact_recovery_min": min(recoveries),
                "perfect_fact_clips": sum(value == 1.0 for value in recoveries),
                "acceptable_naturalness_clips": sum(
                    record["judgment"]["naturalness"] == "acceptable"
                    for record in variant_records
                ),
                "none_or_minor_artifact_clips": sum(
                    record["judgment"]["artifacts"] in {"none", "minor"}
                    for record in variant_records
                ),
            }

        report = {
            "audit_schema": "conditioned_ab_archive_v1",
            "source_archive": archive_path.name,
            "source_archive_bytes": archive_path.stat().st_size,
            "source_archive_sha256": sha256_file(archive_path),
            "archive_entries": len(names),
            "archive_crc_check": "pass",
            "safe_paths": True,
            "run_id": imported_baseline["run_id"],
            "challenge_conditions": challenge["conditions"],
            "development_metric_screen_pass": passing,
            "review_model": summary["model_id"],
            "review_quantization": summary["quantization"],
            "review_records": len(records),
            "audio_hashes_verified": audio_hashes_verified,
            "review_matrix_complete": True,
            "summary_complete": summary["complete"],
            "facts_preserved": facts_preserved,
            "quality_acceptable": quality_acceptable,
            "model_gate_pass": calculated_gate,
            "selection_created": False,
            "heldout_executed": False,
            "conclusion": "no winner: Repeat passed development metrics but failed the conservative model listening gate",
            "variant_review_statistics": variants,
        }
        selected = {
            "summary.json": archive.read("model_review_qwen/summary.json"),
            "protocol.json": archive.read("model_review_qwen/protocol.json"),
            "development_comparisons.csv": archive.read("development_comparisons.csv"),
            "development_listening_queue.csv": archive.read("development_listening_queue.csv"),
            "challenge.json": archive.read("challenge.json"),
            "imported_baseline.json": archive.read("imported_baseline.json"),
            "evidence_scope.json": archive.read("evidence_scope.json"),
        }
        return report, records, selected


def write_evidence(output: Path, report: dict, records: list[dict], selected: dict[str, bytes]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, data in selected.items():
        (output / name).write_bytes(data)
    (output / "archive_audit.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (output / "model_review_results.jsonl").open("w", encoding="utf-8", newline="\n") as target:
        for index, record in enumerate(records):
            retained = {
                "index": index,
                "text_id": record["text_id"],
                "variant": record["variant"],
                "replicate": record["replicate"],
                "condition": record["condition"],
                "audio_sha256": record["audio_sha256"],
                "model_id": record["model_id"],
                "created_utc": record["created_utc"],
                "judgment": record["judgment"],
                "fact_recovery": record["fact_recovery"],
                "fact_details": record["fact_details"],
            }
            target.write(json.dumps(retained, allow_nan=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report, records, selected = audit(args.archive.resolve())
    if args.output:
        write_evidence(args.output, report, records, selected)
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
