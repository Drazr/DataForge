"""Continue A/B evaluation from a copied, frozen Noise-Masking baseline."""

import json
from pathlib import Path

from .experiment import Experiment, digest, file_hash, save_json
from .handoff import copy_once, verify_handoff
from .reporting import export_baseline


def start_delivery(copied_run, output):
    """Import complete baseline rows/audio, without synthesis or ASR calls.

    Raw noise recordings and downloaded evaluator models remain in shared Drive
    at their frozen manifest paths. The baseline input bundle is never changed.
    """
    copied_run = Path(copied_run)
    receipt = verify_handoff(copied_run)
    if not receipt["for_delivery"]:
        raise ValueError("Copy the Noise-Masking run with for_delivery=True")
    manifest = json.loads((copied_run / "manifest.json").read_text())
    experiment = Experiment(manifest["config"], manifest["corpus"], manifest["noise"], output)
    if experiment.fingerprint != receipt["run_id"]:
        raise ValueError("Scoring code, configuration or noise changed; use matching producer/consumer versions")
    expected = {(item["id"], rep, condition) for item in experiment.corpus if item["split"] == "dev"
                for rep in range(experiment.config["replicates"])
                for condition in ["clean"] + [f"{n['id']}_{snr}dB" for n in experiment.noises
                                              for snr in experiment.config["snrs_db"]]}
    records = [json.loads(p.read_text()) for p in sorted((copied_run / "rows").glob("*.json"))]
    keys = [(r["text_id"], r["replicate"], r["condition"]) for r in records]
    if len(keys) != len(set(keys)) or set(keys) != expected or any(
        r["run_id"] != experiment.fingerprint or r["split"] != "dev" or r["variant"] != "baseline" for r in records
    ):
        raise ValueError("The copied development baseline is incomplete or contains unrelated rows")
    receipt_path = experiment.root / "imported_baseline.json"
    # Hash verified content rather than the full receipt: source_directory and
    # audio_path_remap legitimately change when the same Drive folder is mounted
    # from another Google account.
    provenance = {"run_id": receipt["run_id"],
                  "handoff_files_sha256": digest(receipt["files"])}
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text())
        if previous.get("run_id") != provenance["run_id"]:
            raise ValueError("A different baseline was already imported here; choose a new output directory")
        previous_content = previous.get("handoff_files_sha256")
        if previous_content is not None and previous_content != provenance["handoff_files_sha256"]:
            raise ValueError("The baseline content changed after import; choose a new output directory")
    for row in records:
        clip_id = row["clip_id"]
        if Path(clip_id).name != clip_id or "/" in clip_id or "\\" in clip_id:
            raise ValueError("Invalid clip identifier")
        clip_name = Path(row["audio_path"]).name
        copied_clip = copied_run / "clips" / clip_name
        if file_hash(copied_clip) != row["audio_sha256"]:
            raise ValueError("Copied baseline audio hash mismatch")
        output_clip = experiment.root / "clips" / clip_name
        copy_once(copied_clip, output_clip)
        source_name = Path(row["source_audio"]).name
        for suffix in (".wav", ".json"):
            source = (copied_run / "synthesis" / source_name).with_suffix(suffix)
            copy_once(source, (experiment.audio_cache / source_name).with_suffix(suffix))
        row["audio_path"] = str(output_clip)
        row["source_audio"] = str(experiment.audio_cache / source_name)
        path = experiment.root / "rows" / f"{clip_id}.json"
        if path.exists() and json.loads(path.read_text()) != row:
            raise ValueError("Existing baseline row differs from the frozen copy")
        save_json(path, row)
    # Retain the imported request cost; do not overwrite later A/B attempts on resume.
    if not experiment.ledger_path.exists():
        copy_once(copied_run / "synthesis/request_ledger.json", experiment.ledger_path)
    for name in ("evidence_scope.json", "runtime_preflight.json"):
        if (copied_run / name).is_file():
            copy_once(copied_run / name, experiment.root / name)
    save_json(receipt_path, provenance)
    export_baseline(experiment.all_results("dev"), experiment.root, experiment.config["replicates"])
    return experiment
