"""Explicit downloads; archives and models stay outside Git."""

import json
import shutil
import tarfile
from pathlib import Path, PurePosixPath

import requests

from .experiment import file_hash, save_json

MUSAN_URL = "https://www.openslr.org/resources/17/musan.tar.gz"


def download(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return destination
    partial = destination.with_suffix(destination.suffix + ".part")
    with requests.get(url, stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        with partial.open("wb") as target:
            for block in response.iter_content(1024 * 1024):
                if block:
                    target.write(block)
    partial.replace(destination)
    return destination


def download_musan(destination, archive_directory):
    """Download the official ~11 GB archive; retain noise plus four speech files.

    Streaming archive reads avoid loading it into RAM. Only regular files in
    approved directories are copied; no archive links or traversal are accepted.
    Full network download is still necessary; this is not a small remote subset.
    """
    destination, archive_directory = Path(destination), Path(archive_directory)
    archive_directory.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(archive_directory).free < 13 * 1024**3:
        raise RuntimeError("Need at least 13 GiB free for the MUSAN archive")
    destination.mkdir(parents=True, exist_ok=True)
    archive = download(MUSAN_URL, archive_directory / "musan.tar.gz")
    root = destination.resolve()
    count = 0
    with tarfile.open(archive, "r|gz") as members:
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not member.isfile():
                continue
            if not path.parts or path.parts[0] != "musan":
                continue
            is_noise = len(path.parts) > 1 and path.parts[1] == "noise"
            is_speech = len(path.parts) > 1 and path.parts[1] == "speech"
            is_audio = path.suffix.lower() == ".wav"
            keep = is_noise or (is_speech and (not is_audio or count < 4)) or len(path.parts) == 2
            if not keep:
                continue
            target = (root / Path(*path.parts)).resolve()
            if not target.is_relative_to(root):
                raise ValueError("Archive path escaped destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            with members.extractfile(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            if is_speech and is_audio:
                count += 1
    save_json(root / "musan_download.json", {"url": MUSAN_URL, "archive_sha256": file_hash(archive),
              "license": "CC BY 4.0; retain original per-source metadata", "speech_files_retained": count})
    return root / "musan"


def prepare_models(config, model_directory):
    """Resolve immutable revisions once, reuse and hash the downloaded artifacts."""
    from huggingface_hub import HfApi, snapshot_download
    config = dict(config)
    root = Path(model_directory)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / "model_lock.json"
    lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}
    request_id = f"{config['asr_repo']}@{config['asr_revision']}"
    resolved_id = lock.get("asr_requested", "").rsplit("@", 1)[0] + "@" + str(lock.get("asr_revision"))
    if lock and request_id not in {lock["asr_requested"], resolved_id}:
        raise ValueError("Model lock differs from configuration; use another model directory")
    if not lock:
        revision = HfApi().model_info(config["asr_repo"], revision=config["asr_revision"]).sha
        response = requests.get("https://api.github.com/repos/microsoft/DNS-Challenge/commits/master", timeout=30)
        response.raise_for_status()
        lock = {"asr_requested": request_id, "asr_revision": revision, "dnsmos_revision": response.json()["sha"]}
        save_json(lock_path, lock)
    config["asr_local_path"] = snapshot_download(config["asr_repo"], revision=lock["asr_revision"],
                                                cache_dir=str(root / "huggingface"))
    config["asr_revision"] = lock["asr_revision"]
    if config["dnsmos_enabled"]:
        base = f"https://raw.githubusercontent.com/microsoft/DNS-Challenge/{lock['dnsmos_revision']}"
        model = download(base + "/DNSMOS/DNSMOS/sig_bak_ovr.onnx", root / "sig_bak_ovr.onnx")
        download(base + "/LICENSE", root / "DNS-Challenge-LICENSE")
        model_hash = file_hash(model)
        if lock.get("dnsmos_sha256") and lock["dnsmos_sha256"] != model_hash:
            raise ValueError("DNSMOS model hash differs from lock")
        lock["dnsmos_sha256"] = model_hash
        config.update(dnsmos_model_path=str(model), dnsmos_revision=lock["dnsmos_revision"], dnsmos_sha256=model_hash)
        save_json(lock_path, lock)
    return config
