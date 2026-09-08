"""Copy an available review ZIP into this branch; never fabricate a delivery cache."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile


def import_review(archive, root):
    archive, root = Path(archive), Path(root)
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        run_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        rows = json.loads(bundle.read("baseline_rows.json"))
        conditions = ["clean"] + [f"{n['id']}_{snr}dB" for n in manifest["noise"]
                                    for snr in manifest["config"]["snrs_db"]]
        expected = {(item["id"], rep, condition) for item in manifest["corpus"] if item["split"] == "dev"
                    for rep in range(manifest["config"]["replicates"]) for condition in conditions}
        actual = [(r["text_id"], r["replicate"], r["condition"]) for r in rows]
        if len(actual) != len(set(actual)) or set(actual) != expected or any(
                r["run_id"] != run_id or r["split"] != "dev" or r["variant"] != "baseline" for r in rows):
            raise ValueError("Incomplete or unrelated baseline rows")
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive members")
        # Verify every available audio file against its original score.
        available_clips = 0
        for row in rows:
            clip_id = row["clip_id"]
            if Path(clip_id).name != clip_id or "/" in clip_id or "\\" in clip_id:
                raise ValueError("Invalid clip ID")
            name = f"clips/{clip_id}.wav"
            if name in names:
                if hashlib.sha256(bundle.read(name)).hexdigest() != row["audio_sha256"]:
                    raise ValueError(f"Audio hash mismatch: {name}")
                available_clips += 1
        target = root / "inputs/noise_masking_review" / run_id[:16]
        files = {}
        for info in bundle.infolist():
            part = PurePosixPath(info.filename)
            if part.is_absolute() or ".." in part.parts or "\\" in info.filename or ":" in info.filename:
                raise ValueError("Unsafe archive path")
            if info.is_dir():
                continue
            data = bundle.read(info)
            files[info.filename] = hashlib.sha256(data).hexdigest()
            path = target.joinpath(*part.parts)
            if not path.resolve().is_relative_to(target.resolve()):
                raise ValueError("Archive path escapes the evidence directory")
            if path.exists() and path.read_bytes() != data:
                raise ValueError(f"Existing evidence differs: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        receipt = {"source_run_id": run_id, "source_zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                   "baseline_rows": len(rows), "verified_available_clips": available_clips,
                   "complete_delivery_handoff": False,
                   "remaining_from_drive": ["all 210 evaluated clips", "per-clip rows/ JSON files",
                                            "synthesis_cache.json", "cached source speech and metadata", "request_ledger.json"],
                   "files": files}
        (target / "review_copy_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"Copied {len(files)} review files; verified {available_clips} audio clips and {len(rows)} baseline rows.")
        print("Complete delivery handoff still runs in Colab Cell 4 from shared Drive.")
        return target


if __name__ == "__main__":
    import_review(sys.argv[1], Path(__file__).resolve().parents[1])
