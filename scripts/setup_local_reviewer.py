"""Download a pinned free audio reviewer and official Windows llama.cpp runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

REPO = "ggml-org/Qwen2.5-Omni-3B-GGUF"
REVISION = "75f1b73b657a50f5092502799457ccb4a4a1f9df"
FILES = {
    "Qwen2.5-Omni-3B-Q4_K_M.gguf": "4b0bd358c1e9ec55dd3055ef6d71c958c821533d85916a10cfa89c4552a86e29",
    "mmproj-Qwen2.5-Omni-3B-Q8_0.gguf": "4e6c816cd33f7298d07cb780c136a396631e50e62f6501660271f8c6e302e565",
}
RUNTIME = "b10773"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url, path, expected=None):
    if path.exists() and (expected is None or sha256(path) == expected):
        return sha256(path)
    part = path.with_suffix(path.suffix + ".part")
    print(f"Downloading {path.name}", flush=True)
    request = urllib.request.Request(url, headers={"User-Agent": "DataForge-model-review/1"})
    with urllib.request.urlopen(request, timeout=120) as source, part.open("wb") as target:
        count = 0
        last = 0
        while block := source.read(8 * 1024 * 1024):
            target.write(block)
            count += len(block)
            if count - last >= 256 * 1024 * 1024:
                print(f"  {count / 2**20:.0f} MiB", flush=True)
                last = count
    actual = sha256(part)
    if expected and actual != expected:
        raise ValueError(f"Checksum mismatch: {path.name}")
    part.replace(path)
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("models/local_reviewer"))
    parser.add_argument("--backend", choices=["cpu", "vulkan"], default="vulkan")
    args = parser.parse_args()
    root = args.directory.resolve()
    root.mkdir(parents=True, exist_ok=True)
    name = f"llama-{RUNTIME}-bin-win-{args.backend}-x64.zip"
    url = f"https://github.com/ggml-org/llama.cpp/releases/download/{RUNTIME}/{name}"
    hashes = {name: download(url, root / name)}
    with zipfile.ZipFile(root / name) as archive:
        for member in archive.infolist():
            if not (root / "runtime" / member.filename).resolve().is_relative_to(root / "runtime"):
                raise ValueError("Unsafe runtime archive member")
        archive.extractall(root / "runtime")
    for filename, expected in FILES.items():
        hashes[filename] = download(
            f"https://huggingface.co/{REPO}/resolve/{REVISION}/{filename}", root / filename, expected
        )
    receipt = {"model_repo": REPO, "model_revision": REVISION, "runtime": RUNTIME,
               "backend": args.backend, "sha256": hashes}
    (root / "setup_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("Ready:", root, flush=True)


if __name__ == "__main__":
    main()
