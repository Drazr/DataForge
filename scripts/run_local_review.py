"""Start a private local audio server, review the bundle, and stop the server."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models/local_reviewer")
    parser.add_argument("--gpu-layers", type=int, default=12)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    executable = args.model_dir / "runtime/llama-server.exe"
    command = [str(executable), "-m", str(args.model_dir / "Qwen2.5-Omni-3B-Q4_K_M.gguf"),
               "--mmproj", str(args.model_dir / "mmproj-Qwen2.5-Omni-3B-Q8_0.gguf"),
               "--host", "127.0.0.1", "--port", str(args.port), "--alias", "local-audio-reviewer",
               "-c", "4096", "-np", "1", "-ngl", str(args.gpu_layers), "-t", "4", "-b", "256", "-ub", "128",
               "-n", "160", "--reasoning", "off",
               "--jinja"]
    endpoint = f"http://127.0.0.1:{args.port}"
    # Refuse to attach to an existing unidentified server.
    try:
        with urllib.request.urlopen(endpoint + "/health", timeout=2):
            raise RuntimeError("Port already serves a model; choose another --port")
    except OSError:
        pass
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    with (args.output / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        try:
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError(f"Audio server exited {server.returncode}; inspect server.log")
                try:
                    with urllib.request.urlopen(endpoint + "/health", timeout=3) as response:
                        if json.load(response).get("status") == "ok":
                            break
                except OSError:
                    pass
                time.sleep(2)
            else:
                raise TimeoutError("Audio server did not become ready")
            (args.output / "server_settings.json").write_text(json.dumps({
                "gpu_layers": args.gpu_layers, "context": 4096, "parallel": 1, "threads": 4,
                "batch": 256, "microbatch": 128, "max_output_tokens": 160, "reasoning": "off", "projector_offload": True,
                "backend": "llama.cpp Vulkan", "runtime": "b10773",
            }, indent=2), encoding="utf-8")
            review = [sys.executable, str(ROOT / "scripts/review_development_audio.py"), str(args.bundle),
                      "--output", str(args.output), "--endpoint", endpoint + "/v1/chat/completions",
                      "--setup-receipt", str(args.model_dir / "setup_receipt.json")]
            if args.limit is not None:
                review += ["--limit", str(args.limit)]
            subprocess.run(review, check=True)
        finally:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == "__main__":
    main()
