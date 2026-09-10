"""Deterministic MUSAN panel selection for the v2 breakpoint grid."""

import random
from pathlib import Path

import numpy as np
import soundfile as sf

from .experiment import audio_read_window, file_hash, rms


SELECTION_BASIS = "deterministic_musan_panel_v1"
SOURCE = "https://www.openslr.org/17/"
LICENSE = "CC BY 4.0"


def _eligible(path, root, excluded_hashes, used_hashes, minimum_window_seconds):
    try:
        info = sf.info(path)
        if info.duration < 2 * minimum_window_seconds:
            return None, "shorter than two frozen windows"
        offset_b_s = info.duration - minimum_window_seconds
        windows = [
            audio_read_window(path, offset, minimum_window_seconds, 8000)[0]
            for offset in (0.0, offset_b_s)
        ]
        if any(rms(window) < 1e-5 for window in windows):
            return None, "silent window"
        if any(float(np.max(np.abs(window))) >= 0.9995 for window in windows):
            return None, "clipped window"
        sha256 = file_hash(path)
        if sha256 in excluded_hashes:
            return None, "used by pilot baseline"
        if sha256 in used_hashes:
            return None, "duplicate audio hash"
        return {
            "path": str(path),
            "relative_path": path.relative_to(root).as_posix(),
            "sha256": sha256,
            "duration_s": info.duration,
            "sample_rate": info.samplerate,
            "offset_s": 0.0,
            "offset_b_s": offset_b_s,
            "minimum_window_s": minimum_window_seconds,
            "source": SOURCE,
            "license": LICENSE,
            "verified_by_listening": False,
            "selection_basis": SELECTION_BASIS,
        }, None
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def select_noise_panel(musan_root, *, seed, excluded_hashes=(), minimum_window_seconds=20.0):
    """Choose two speech and two environmental recordings before score inspection."""
    root = Path(musan_root).resolve()
    if minimum_window_seconds <= 0:
        raise ValueError("minimum_window_seconds must be positive")
    groups = {
        "speech": (sorted(root.glob("speech/**/*.wav")), "competing_speech"),
        "environment": (sorted(root.glob("noise/**/*.wav")), "environmental_noise"),
    }
    if any(len(paths) < 2 for paths, _ in groups.values()):
        raise ValueError("A complete MUSAN copy with speech and noise recordings is required")
    excluded_hashes, used_hashes = set(excluded_hashes), set()
    selected, rejected = [], []
    for family, (paths, kind) in groups.items():
        order = list(paths)
        random.Random(f"{seed}:{family}").shuffle(order)
        family_selected = []
        for path in order:
            record, reason = _eligible(
                path, root, excluded_hashes, used_hashes, minimum_window_seconds
            )
            if record is None:
                rejected.append({"relative_path": path.relative_to(root).as_posix(), "reason": reason})
                continue
            used_hashes.add(record["sha256"])
            record.update(id=f"{family}_{len(family_selected) + 1}", kind=kind)
            family_selected.append(record)
            if len(family_selected) == 2:
                break
        if len(family_selected) != 2:
            raise ValueError(f"Could not select two eligible {family} recordings")
        selected.extend(family_selected)
    return selected, {
        "selection_basis": SELECTION_BASIS,
        "seed": seed,
        "minimum_window_seconds": minimum_window_seconds,
        "excluded_hashes": sorted(excluded_hashes),
        "selected": [{k: v for k, v in row.items() if k != "path"} for row in selected],
        "rejected_before_completion": rejected,
    }
