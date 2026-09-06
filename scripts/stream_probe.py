"""Measure an actual uncached Rime HTTP PCMU stream; this does not place calls."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataforge.experiment import request_audio, save_json, validate_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="experiment.json")
    parser.add_argument("--output", default="outputs/stream-probe")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error("Use between 1 and 10 repeats")
    config = json.loads(Path(args.config).read_text())
    key = os.environ.get("RIME_API_KEY")
    if not key:
        parser.error("Set RIME_API_KEY securely in the environment")
    validate_catalog(config)
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    texts = ["Your reference code is seven two nine four. Do not cancel the appointment.",
             "Your appointment is Tuesday at three thirty p m. " * 8 + "The final word is complete."]
    rows = []
    for index, text in enumerate(texts):
        for repeat in range(args.repeats):
            target = root / f"stream_{index}_{repeat}.ulaw"
            if target.exists():
                raise ValueError("Use a new output directory for an uncached streaming run")
            payload = {"text": text, "modelId": config["model_id"], "speaker": config["speaker"],
                       "lang": config["language"], "samplingRate": 8000, "timeScaleFactor": 1.0}
            data, metrics = request_audio(key, payload, config["endpoint"], "audio/PCMU", 160)
            if data.startswith((b"RIFF", b"{")):
                raise ValueError("Expected headerless PCMU")
            target.write_bytes(data)
            rows.append({**metrics, "payload": payload, "endpoint": config["endpoint"], "repeat": repeat,
                         "audio_path": str(target), "payload_duration_s": len(data) / 8000,
                         "speech_completion_verified": False, "playback_gap_verified": False})
            save_json(root / "stream_results.json", rows)
            print(f"Saved stream {index}, repeat {repeat}; first client chunk {metrics['client_first_chunk_s']:.3f}s")
    print("Decode/listen/transcribe to verify endings. Network chunk gaps are NOT audible playback gaps.")


if __name__ == "__main__":
    main()
