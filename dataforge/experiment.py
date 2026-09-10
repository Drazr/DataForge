"""Reproducible audio A/B harness. No credentials are persisted in artifacts."""

import hashlib
import io
import json
import math
import re
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import soundfile as sf
from scipy.signal import resample_poly


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    temp.replace(path)


def normalize(text):
    # Keep word boundaries; do not silently equate a different digit or name.
    text = text.lower().replace("don't", "do not").replace("can't", "cannot")
    return " ".join(re.findall(r"[a-z0-9]+", text))


def contains(text, phrase):
    return f" {normalize(phrase)} " in f" {normalize(text)} "


def canonicalize_time(text):
    """Equate numeric clock formatting only when an explicit AM/PM is present."""
    pattern = (r"(?<![\w:.\-])(?P<hour>1[0-2]|0?[1-9])[:.\-]?\s*"
               r"(?P<minute>[0-5][0-9])\s*(?P<period>[ap])\.?\s*m\.?(?!\w)")
    return re.sub(pattern, lambda m: f"{int(m['hour'])}:{m['minute']} {m['period'].lower()}m",
                  text, flags=re.IGNORECASE)


def fact_score(transcript, facts):
    details = {}
    for fact in facts:
        match_text = canonicalize_time(transcript) if fact["id"] == "time" else transcript
        match_phrase = canonicalize_time if fact["id"] == "time" else lambda value: value
        found = any(contains(match_text, match_phrase(alias)) for alias in fact["aliases"])
        conflict = any(contains(match_text, match_phrase(phrase)) for phrase in fact.get("forbidden", []))
        # A correct negative phrase beside its affirmative counterpart is not recovery.
        if fact.get("negative_proposition"):
            words = normalize(transcript)
            proposition = normalize(fact["negative_proposition"])
            for match in re.finditer(r"\b" + re.escape(proposition) + r"\b", words):
                if not words[:match.start()].rstrip().endswith("not"):
                    conflict = True
        details[fact["id"]] = {"recovered": bool(found and not conflict), "conflict": conflict}
    return (sum(x["recovered"] for x in details.values()) / len(details) if details else None), details


def load_corpus(path):
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    assert len({x["id"] for x in items}) == len(items), "Duplicate text IDs"
    seen = set()
    for item in items:
        assert item["split"] in {"dev", "heldout"}
        assert normalize(item["text"]) not in seen, "Duplicate text across splits"
        seen.add(normalize(item["text"]))
        for variant in ("text", "clauses", "repeat"):
            score, _ = fact_score(item[variant], item["facts"])
            assert score in (None, 1.0), f"Fact missing in {item['id']} / {variant}"
    return items


def audio_read(path, rate=None):
    audio, sr = sf.read(path, dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if not len(audio) or not np.isfinite(audio).all():
        raise ValueError(f"Empty or invalid audio: {path}")
    if rate and rate != sr:
        divisor = math.gcd(sr, rate)
        audio = resample_poly(audio, rate // divisor, sr // divisor).astype(np.float32)
        sr = rate
    return audio, sr


def audio_read_window(path, offset_s, duration_s, rate=8000):
    """Read one bounded source window without loading a long recording into RAM."""
    with sf.SoundFile(path) as source:
        start = round(offset_s * source.samplerate)
        frames = round(duration_s * source.samplerate)
        if start < 0 or start + frames > len(source):
            raise ValueError("Requested audio window is outside the source clip")
        source.seek(start)
        audio = source.read(frames, dtype="float32", always_2d=True).mean(axis=1)
        sr = source.samplerate
    if not len(audio) or not np.isfinite(audio).all():
        raise ValueError(f"Empty or invalid audio window: {path}")
    if rate != sr:
        divisor = math.gcd(sr, rate)
        audio = resample_poly(audio, rate // divisor, sr // divisor).astype(np.float32)
    return audio, rate


def rms(audio):
    return float(np.sqrt(np.mean(np.asarray(audio, dtype=np.float64) ** 2)))


def level(audio, target_dbfs):
    energy = rms(audio)
    if energy < 1e-8:
        raise ValueError("Cannot level silent audio")
    scaled = audio * (10 ** (target_dbfs / 20) / energy)
    if np.max(np.abs(scaled)) >= 0.99:
        raise ValueError("Speech leveling clips; lower speech_rms_dbfs for the whole experiment")
    return scaled


def active_rms(audio, sample_rate=8000):
    """RMS of 20 ms frames within 40 dB of peak frame power; not ITU P.56.

    Reject silence and exclude quiet frames so added pauses do not raise speech
    gain. Frame parameters are fixed across variants and recorded in each run.
    """
    audio = np.asarray(audio, dtype=np.float64)
    if not len(audio) or not np.isfinite(audio).all():
        raise ValueError("Empty or invalid speech")
    size = max(1, round(sample_rate * 0.020))
    starts = np.arange(0, len(audio), size)
    counts = np.minimum(size, len(audio) - starts)
    powers = np.add.reduceat(audio ** 2, starts) / counts
    if powers.max() < 1e-16:
        raise ValueError("Silent speech")
    active = powers >= powers.max() * 10 ** (-40 / 10)
    return float(np.sqrt(np.average(powers[active], weights=counts[active])))


def level_active(audio, target_dbfs, sample_rate=8000):
    scaled = audio * (10 ** (target_dbfs / 20) / active_rms(audio, sample_rate))
    if np.max(np.abs(scaled)) >= 0.99:
        raise ValueError("Speech leveling clips; lower speech_rms_dbfs for the whole experiment")
    return scaled


def phone_roundtrip(audio, sample_rate):
    """One local G.711 mu-law encode/decode cycle, not a real provider call."""
    sf_buffer = io.BytesIO()
    sf.write(sf_buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
    encoded = subprocess.run(
        [os.environ.get("FFMPEG_BINARY", "ffmpeg"), "-v", "error", "-i", "pipe:0", "-ar", "8000", "-ac", "1",
         "-f", "mulaw", "pipe:1"], input=sf_buffer.getvalue(), capture_output=True, check=True,
    ).stdout
    decoded = subprocess.run(
        [os.environ.get("FFMPEG_BINARY", "ffmpeg"), "-v", "error", "-f", "mulaw", "-ar", "8000", "-ac", "1",
         "-i", "pipe:0", "-f", "f32le", "pipe:1"],
        input=encoded, capture_output=True, check=True,
    ).stdout
    return np.frombuffer(decoded, dtype="<f4").copy()


def noise_window(audio, length, offset, *, wrap=True):
    if offset < 0 or offset >= len(audio):
        raise ValueError("Noise offset is outside the source clip")
    if not wrap and offset + length > len(audio):
        raise ValueError("Noise source is too short for the frozen non-looping window")
    if not wrap:
        return np.asarray(audio[offset:offset + length], dtype=np.float32), False
    # Pilot compatibility: same offset and deterministic wrap across variants.
    indices = (np.arange(length) + offset) % len(audio)
    return audio[indices], offset + length > len(audio)


def mix_noise(speech, noise, snr_db, *, speech_reference_rms=None, noise_reference_rms=None):
    if rms(speech) < 1e-8 or rms(noise) < 1e-8:
        raise ValueError("Silent speech or noise")
    speech_reference = rms(speech) if speech_reference_rms is None else speech_reference_rms
    noise_reference = rms(noise) if noise_reference_rms is None else noise_reference_rms
    if not np.isfinite([speech_reference, noise_reference, snr_db]).all() or min(speech_reference, noise_reference) <= 0:
        raise ValueError("Invalid SNR calibration")
    scaled_noise = noise * (speech_reference / (noise_reference * 10 ** (snr_db / 20)))
    mixture = speech + scaled_noise
    # Reject instead of giving one variant a different limiter/gain policy.
    if np.max(np.abs(mixture)) >= 0.99:
        raise ValueError("Mixture would clip: lower speech_rms_dbfs globally and start a new run")
    measured = 20 * np.log10(speech_reference / rms(scaled_noise))
    return mixture.astype(np.float32), float(measured)


def safe_speech_level_dbfs(speeches, noise_sources, snrs_db, preferred_dbfs,
                           *, peak_limit=0.90, step_db=0.5):
    """Choose one pre-score speech level that keeps the complete exact grid below peak_limit."""
    if not speeches or not noise_sources or not snrs_db:
        raise ValueError("Safe-level audit requires speech, noise, and SNR inputs")
    if not 0 < peak_limit < 0.99 or step_db <= 0:
        raise ValueError("Invalid safe-level audit parameters")
    worst_unit_peak = 0.0
    for speech in speeches:
        speech = np.asarray(speech, dtype=np.float64)
        speech_unit = speech / active_rms(speech)
        worst_unit_peak = max(worst_unit_peak, float(np.max(np.abs(speech_unit))))
        for noise in noise_sources:
            segment = np.asarray(noise[:len(speech)], dtype=np.float64)
            if len(segment) != len(speech) or rms(segment) < 1e-8:
                raise ValueError("Noise source is too short or silent for safe-level audit")
            noise_unit = segment / rms(segment)
            for snr_db in snrs_db:
                mixture_unit = speech_unit + noise_unit / 10 ** (snr_db / 20)
                worst_unit_peak = max(worst_unit_peak, float(np.max(np.abs(mixture_unit))))
    ceiling_dbfs = 20 * math.log10(peak_limit / worst_unit_peak)
    rounded_ceiling = math.floor(ceiling_dbfs / step_db) * step_db
    chosen = min(float(preferred_dbfs), rounded_ceiling)
    if chosen < -50:
        raise ValueError("Selected noise has pathological crest factor; freeze a new panel before scoring")
    predicted_peak = worst_unit_peak * 10 ** (chosen / 20)
    return chosen, {"preferred_dbfs": float(preferred_dbfs), "chosen_dbfs": chosen,
                    "peak_limit": peak_limit, "step_db": step_db,
                    "worst_unit_peak": worst_unit_peak,
                    "predicted_max_peak": predicted_peak}


def noise_failure_evidence(frame, replicates):
    """Same fact lost in noise but recovered cleanly, for every repeat of a text."""
    base = frame[(frame.split == "dev") & (frame.variant == "baseline")]
    keys = ["text_id", "replicate"]
    if base.duplicated(keys + ["condition"]).any():
        raise ValueError("Duplicate baseline rows")
    clean = base[base.condition == "clean"]
    noisy = base[base.condition != "clean"]
    pairs = noisy.merge(clean, on=keys, suffixes=("_noisy", "_clean"), validate="many_to_one")
    records = []
    for pair in pairs.to_dict("records"):
        for fact_id, detail in pair["fact_details_noisy"].items():
            if not detail["recovered"] and pair["fact_details_clean"].get(fact_id, {}).get("recovered"):
                records.append({"text_id": pair["text_id"], "replicate": pair["replicate"],
                                "condition": pair["condition_noisy"], "fact_id": fact_id,
                                "clean_clip_id": pair["clip_id_clean"], "noisy_clip_id": pair["clip_id_noisy"],
                                "clean_audio_path": pair["audio_path_clean"], "audio_path": pair["audio_path_noisy"]})
    result = pd.DataFrame(records, columns=["text_id", "replicate", "condition", "fact_id",
                                           "clean_clip_id", "noisy_clip_id", "clean_audio_path", "audio_path"])
    if result.empty:
        return result
    expected = set(range(replicates))
    return result.groupby(["text_id", "condition", "fact_id"]).filter(
        lambda group: set(group.replicate) == expected).reset_index(drop=True)


def validate_challenges(frame, conditions, replicates):
    if not 1 <= len(conditions) <= 2 or len(set(conditions)) != len(conditions) or "clean" in conditions:
        raise ValueError("Choose one or two unique noisy development conditions")
    evidence = noise_failure_evidence(frame, replicates)
    for condition in conditions:
        if evidence[evidence.condition == condition].text_id.nunique() < 2:
            raise ValueError("Each challenge needs two texts with the same fact lost in every repeat, recovered in the matched clean clips")
    return evidence[evidence.condition.isin(conditions)]


def validate_catalog(config):
    url = "https://users.rime.ai/data/voices/all-v2.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    catalog = response.json()
    lang = {"en": "eng", "hi": "hin"}.get(config["language"], config["language"])
    speakers = catalog.get(config["model_id"], {}).get(lang, [])
    if config["speaker"] not in speakers:
        raise ValueError("Configured model/voice/language not in live catalog; inspect catalog before continuing")
    return {"url": url, "sha256": digest(catalog), "checked_utc": datetime.now(timezone.utc).isoformat()}


def request_audio(key, payload, endpoint, accept="audio/wav", chunk_size=512):
    if not endpoint.startswith("https://"):
        raise ValueError("Rime endpoint must use HTTPS")
    start = time.perf_counter()
    times, chunks = [], []
    # No automatic retries of a billed POST. A failed request may have been billed.
    with requests.post(endpoint, headers={"Authorization": f"Bearer {key}", "Accept": accept},
                       json=payload, stream=True, timeout=(15, 120), allow_redirects=False) as response:
        if response.status_code != 200:
            raise RuntimeError(f"Rime HTTP {response.status_code}; request was not retried")
        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type or "text/" in content_type:
            raise RuntimeError("Rime returned non-audio content")
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                times.append(time.perf_counter() - start)
                chunks.append(chunk)
    if not chunks:
        raise RuntimeError("Empty Rime response")
    metrics = {"client_first_chunk_s": times[0], "response_complete_s": times[-1],
               "chunk_arrival_s": times, "chunk_bytes": [len(c) for c in chunks],
               "max_client_interchunk_s": float(max(np.diff(times), default=0)),
               "http_complete": True, "accept": accept, "content_type": content_type}
    return b"".join(chunks), metrics


class Experiment:
    def __init__(self, config, corpus, noises, output, *, synthesis_cache_root=None):
        self.config, self.corpus = dict(config), corpus
        self.mixing_protocol = config.get("mixing_protocol", "source_rms_wrap_v1")
        if self.mixing_protocol not in {"source_rms_wrap_v1", "window_rms_no_wrap_v2"}:
            raise ValueError("Unknown mixing protocol")
        self.noises = []
        for entry in noises:
            deterministic_panel = entry.get("selection_basis") == "deterministic_musan_panel_v1"
            if not entry.get("verified_by_listening") and not deterministic_panel:
                raise ValueError("Noise sources need listening verification or the frozen deterministic MUSAN panel protocol")
            if self.mixing_protocol == "window_rms_no_wrap_v2":
                audio, _ = audio_read_window(
                    entry["path"], entry["offset_s"], entry["minimum_window_s"], 8000
                )
                sample_offset_s = entry["offset_s"]
            else:
                audio, _ = audio_read(entry["path"], 8000)
                sample_offset_s = 0.0
            if rms(audio) < 1e-8:
                raise ValueError("Silent noise file")
            if self.mixing_protocol != "window_rms_no_wrap_v2" and not 0 <= entry["offset_s"] * 8000 < len(audio):
                raise ValueError("Noise offset is outside the source clip")
            self.noises.append({**entry, "sha256": file_hash(entry["path"]), "samples": audio,
                                "samples_offset_s": sample_offset_s, "reference_rms": rms(audio)})
        if len({n["id"] for n in noises}) != len(noises) or len(noises) < 2:
            raise ValueError("Provide at least two uniquely named noise sources")
        if config["model_id"] != "coda" or config["phone_sample_rate"] != 8000:
            raise ValueError("This experiment pins Coda and a simulated 8 kHz PCMU path")
        self.level_method = "20ms_frames_within_40dB_of_peak_power_v1"
        snr_definition = ("active speech RMS / extracted noise-window RMS; no wrapping"
                          if self.mixing_protocol == "window_rms_no_wrap_v2"
                          else "active speech RMS / full noise source RMS; fixed noise gain across durations")
        manifest = {"config": config, "corpus": corpus, "implementation_sha256": file_hash(__file__),
                    "speech_level_method": self.level_method,
                    "snr_definition": snr_definition,
                    "noise": [{k: v for k, v in n.items() if k not in {"samples", "samples_offset_s"}}
                              for n in self.noises]}
        self.fingerprint = digest(manifest)
        self.root = Path(output) / self.fingerprint[:16]
        self.root.mkdir(parents=True, exist_ok=True)
        save_json(self.root / "manifest.json", manifest)
        # Shared across evaluation grids; payload+replicate still determines each WAV.
        synthesis_scope = {k: config[k] for k in ("endpoint", "model_id", "speaker", "language", "sample_rate")}
        synthesis_scope["protocol"] = "rime_wav_v1"
        cache_root = Path(synthesis_cache_root) if synthesis_cache_root else Path(output) / "synthesis_cache"
        self.audio_cache = cache_root / digest(synthesis_scope)[:16]
        self.audio_cache.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.audio_cache / "request_ledger.json"
        save_json(self.root / "synthesis_cache.json", {"path": str(self.audio_cache), "scope": synthesis_scope,
                                                     "ledger_path": str(self.ledger_path)})
        self._asr = None
        self._dnsmos = None

    def variant(self, item, name):
        if name not in {"baseline", "clauses", "repeat", "slow"}:
            raise ValueError("Unknown intervention")
        text = item[{"baseline": "text", "slow": "text", "clauses": "clauses", "repeat": "repeat"}[name]]
        speed = self.config["slowdown"] if name == "slow" else 1.0
        return text, speed

    def synthesize(self, item, variant, replicate, key):
        text, speed = self.variant(item, variant)
        payload = {"text": text, "modelId": self.config["model_id"], "speaker": self.config["speaker"],
                   "lang": self.config["language"], "samplingRate": self.config["sample_rate"],
                   "timeScaleFactor": speed}
        cache_id = digest({"payload": payload, "replicate": replicate, "endpoint": self.config["endpoint"]})
        path = self.audio_cache / f"{cache_id}.wav"
        meta_path = path.with_suffix(".json")
        if path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text())
            if file_hash(path) != meta["sha256"]:
                raise ValueError("Cached synthesis hash mismatch")
            return path, {**meta, "cached": True}
        if len(text) > 1000:
            raise ValueError("Rime request exceeds 1,000 characters")
        ledger_path = self.ledger_path
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
        used = sum(x["characters"] for x in ledger)
        if used + len(text) > self.config["max_request_characters"]:
            raise RuntimeError("Character budget reached; review request_ledger.json before increasing it")
        ledger.append({"cache_id": cache_id, "run_id": self.fingerprint, "characters": len(text),
                       "attempt_utc": datetime.now(timezone.utc).isoformat()})
        save_json(ledger_path, ledger)
        data, metrics = request_audio(key, payload, self.config["endpoint"])
        if not data.startswith(b"RIFF"):
            raise ValueError("Expected a RIFF WAV response")
        audio, sr = sf.read(io.BytesIO(data), dtype="float32")
        if sr != self.config["sample_rate"] or audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
            raise ValueError("Unexpected sample rate, channel count, or invalid audio")
        path.write_bytes(data)
        meta = {**metrics, "payload": payload, "sha256": file_hash(path), "cached": False,
                "duration_s": len(audio) / sr, "raw_peak": float(np.max(np.abs(audio))),
                "synthesized_utc": datetime.now(timezone.utc).isoformat()}
        save_json(meta_path, meta)
        return path, meta

    def synthesis_cache_paths(self, item, variant, replicate):
        """Return cached WAV/metadata paths without making a billed request."""
        text, speed = self.variant(item, variant)
        payload = {"text": text, "modelId": self.config["model_id"], "speaker": self.config["speaker"],
                   "lang": self.config["language"], "samplingRate": self.config["sample_rate"],
                   "timeScaleFactor": speed}
        cache_id = digest({"payload": payload, "replicate": replicate, "endpoint": self.config["endpoint"]})
        path = self.audio_cache / f"{cache_id}.wav"
        return path, path.with_suffix(".json")

    def transcribe(self, path):
        from faster_whisper import WhisperModel
        if self._asr is None:
            # The notebook resolves an immutable HF snapshot before constructing Experiment.
            self._asr = WhisperModel(self.config["asr_local_path"], device=self.config["asr_device"],
                                     compute_type=self.config["asr_compute_type"])
        segments, _ = self._asr.transcribe(str(path), language="en", beam_size=self.config["asr_beam_size"],
                                           temperature=0, vad_filter=False, condition_on_previous_text=False)
        return " ".join(segment.text.strip() for segment in segments)

    def quality(self, audio, sr):
        if not self.config["dnsmos_enabled"]:
            return {"dnsmos_sig": None, "dnsmos_bak": None, "dnsmos_ovrl": None}
        # Microsoft non-personalized DNSMOS P.835, waveform model + published calibration.
        import onnxruntime as ort
        if self._dnsmos is None:
            self._dnsmos = ort.InferenceSession(self.config["dnsmos_model_path"], providers=["CPUExecutionProvider"])
        if sr != 16000:
            audio = resample_poly(audio, 16000 // math.gcd(sr, 16000), sr // math.gcd(sr, 16000))
        length = int(9.01 * 16000)
        while len(audio) < length:
            audio = np.tile(audio, 2)
        values = []
        for start in range(0, len(audio) - length + 1, 16000):
            window = audio[start:start + length].astype(np.float32)[None, :]
            sig, bak, overall = self._dnsmos.run(None, {self._dnsmos.get_inputs()[0].name: window})[0][0]
            values.append([np.polyval([-0.08397278, 1.22083953, 0.0052439], sig),
                           np.polyval([-0.13166888, 1.60915514, -0.39604546], bak),
                           np.polyval([-0.06766283, 1.11546468, 0.04602535], overall)])
        scores = np.mean(values, axis=0)
        return dict(zip(["dnsmos_sig", "dnsmos_bak", "dnsmos_ovrl"], map(float, scores)))

    def run(self, split, variants, key, *, item_ids=None, noise_ids=None, snrs=None, include_clean=True):
        from jiwer import wer
        from pystoi import stoi
        if split not in {"dev", "heldout"}:
            raise ValueError("Unknown split")
        if split == "heldout":
            decision = json.loads((self.root / "selection.json").read_text())
            if set(variants) != {"baseline", decision["variant"]}:
                raise ValueError("Held-out evaluation must use only the frozen candidate and baseline")
        item_ids = set(item_ids) if item_ids is not None else None
        selected_noises = [noise for noise in self.noises if noise_ids is None or noise["id"] in set(noise_ids)]
        selected_snrs = list(self.config["snrs_db"] if snrs is None else snrs)
        if noise_ids is not None and {noise["id"] for noise in selected_noises} != set(noise_ids):
            raise ValueError("Unknown requested noise ID")
        if not set(selected_snrs).issubset(self.config["snrs_db"]):
            raise ValueError("Requested SNR is outside the frozen grid")
        rows = []
        jobs = [(item, variant, rep) for item in self.corpus
                if item["split"] == split and (item_ids is None or item["id"] in item_ids)
                for variant in variants for rep in range(self.config["replicates"])]
        if item_ids is not None and {item["id"] for item, _, _ in jobs} != item_ids:
            raise ValueError("Unknown requested text ID")
        np.random.default_rng(self.config["seed"]).shuffle(jobs)
        for index, (item, variant, rep) in enumerate(jobs):
            original, synth = self.synthesize(item, variant, rep, key)
            source_audio_sha256 = file_hash(original)
            speech, sr = audio_read(original)
            phone = level_active(phone_roundtrip(speech, sr), self.config["speech_rms_dbfs"])
            cases = ([("clean", None, None)] if include_clean else []) + [
                (noise["id"], snr, noise) for noise in selected_noises for snr in selected_snrs
            ]
            for noise_id, snr, noise in cases:
                condition = "clean" if snr is None else f"{noise_id}_{snr}dB"
                clip_id = f"{item['id']}_{variant}_r{rep}_{condition}"
                result_path = self.root / "rows" / f"{clip_id}.json"
                if result_path.exists():
                    previous = json.loads(result_path.read_text())
                    if file_hash(previous["audio_path"]) != previous["audio_sha256"]:
                        raise ValueError("Saved evaluated audio changed; restore the original before resuming")
                    rows.append(previous)
                    continue
                mixture, measured, looped = phone, None, False
                speech_reference, window_reference, noise_gain = active_rms(phone), None, None
                if noise is not None:
                    segment, looped = noise_window(
                        noise["samples"], len(phone),
                        int((noise["offset_s"] - noise["samples_offset_s"]) * 8000),
                        wrap=self.mixing_protocol != "window_rms_no_wrap_v2",
                    )
                    window_reference = rms(segment)
                    calibration_reference = (window_reference if self.mixing_protocol == "window_rms_no_wrap_v2"
                                             else noise["reference_rms"])
                    noise_gain = speech_reference / (calibration_reference * 10 ** (snr / 20))
                    mixture, measured = mix_noise(phone, segment, snr,
                                                 speech_reference_rms=speech_reference,
                                                 noise_reference_rms=calibration_reference)
                    if self.mixing_protocol == "window_rms_no_wrap_v2" and abs(measured - snr) > 0.1:
                        raise ValueError("Measured SNR differs from the frozen request by more than 0.1 dB")
                path = self.root / "clips" / f"{clip_id}.wav"
                path.parent.mkdir(exist_ok=True)
                sf.write(path, mixture, 8000, subtype="FLOAT")
                transcript = self.transcribe(path)
                text, speed = self.variant(item, variant)
                facts, details = fact_score(transcript, item["facts"])
                result = {"run_id": self.fingerprint, "clip_id": clip_id, "text_id": item["id"], "split": split, "variant": variant,
                          "replicate": rep, "condition": condition, "noise_id": noise_id, "snr_db": snr,
                          "measured_snr_db": measured, "noise_file": noise["path"] if noise else None,
                          "noise_sha256": noise["sha256"] if noise else None,
                          "noise_offset_s": noise["offset_s"] if noise else None, "noise_looped": looped,
                          "noise_kind": noise.get("kind", noise_id) if noise else "clean",
                          "noise_reference_rms": noise["reference_rms"] if noise else None,
                          "noise_window_rms": window_reference, "noise_gain": noise_gain,
                          "mixing_protocol": self.mixing_protocol,
                          "speech_level_method": self.level_method, "sample_rate": 8000,
                          "speech_active_rms_dbfs": 20 * math.log10(speech_reference),
                          "snr_definition": ("active speech / extracted noise-window RMS; no wrapping"
                                             if self.mixing_protocol == "window_rms_no_wrap_v2"
                                             else "active speech / full source noise RMS; fixed gain"),
                          "reference_text": text, "transcript": transcript,
                          "wer": float(wer(normalize(text), normalize(transcript))),
                          "fact_recovery": facts, "fact_details": details, "fact_count": len(item["facts"]),
                          "facts_recovered": sum(x["recovered"] for x in details.values()),
                          "estoi": float(stoi(phone, mixture, 8000, extended=True)) if noise else None,
                          "duration_s": len(phone) / 8000, "format_duration_delta_s": len(phone) / 8000 - len(speech) / sr,
                          "audio_path": str(path), "audio_sha256": file_hash(path), "source_audio": str(original),
                          "source_audio_sha256": source_audio_sha256,
                          "raw_peak": synth["raw_peak"], "synthesis_cached": synth["cached"],
                          "client_first_chunk_s": None if synth["cached"] else synth["client_first_chunk_s"],
                          "time_scale_factor": speed, "transport": "HTTP WAV -> local PCMU roundtrip",
                          "noise_placement": "after simulated phone codec", "model_id": self.config["model_id"],
                          "speaker": self.config["speaker"], "endpoint": self.config["endpoint"],
                          **self.quality(mixture, 8000)}
                save_json(result_path, result)
                rows.append(result)
            print(f"{split}: {index + 1}/{len(jobs)} syntheses scored", flush=True)
        frame = pd.DataFrame(rows)
        frame.to_csv(self.root / f"{split}_{'-'.join(variants)}.csv", index=False)
        return frame

    def all_results(self, split):
        records = [json.loads(p.read_text()) for p in sorted((self.root / "rows").glob("*.json"))]
        return pd.DataFrame([r for r in records if r["split"] == split])

    def comparisons(self, frame, conditions=None):
        if conditions is not None:
            frame = frame[frame.condition.isin(conditions)]
        base = frame[frame.variant == "baseline"]
        keys = ["text_id", "replicate", "condition"]
        reports = []
        for variant in sorted(set(frame.variant) - {"baseline"}):
            other = frame[frame.variant == variant]
            pairs = base.merge(other, on=keys, suffixes=("_base", "_new"), validate="one_to_one")
            if len(pairs) != len(base) or len(pairs) != len(other):
                raise ValueError("Incomplete paired results; finish this run before selection")
            critical = pairs[pairs.fact_count_base > 0]
            fact_gain = float((critical.fact_recovery_new - critical.fact_recovery_base).mean())
            wer_delta = float((pairs.wer_new - pairs.wer_base).mean())
            ratio = float((pairs.duration_s_new / pairs.duration_s_base).mean())
            quality = pairs.dnsmos_ovrl_new.notna().all() and pairs.dnsmos_ovrl_base.notna().all()
            mos_delta = float((pairs.dnsmos_ovrl_new - pairs.dnsmos_ovrl_base).mean()) if quality else None
            passes = (np.isfinite(fact_gain) and fact_gain >= self.config["minimum_fact_gain"]
                      and wer_delta <= self.config["maximum_wer_increase"]
                      and ratio <= self.config["maximum_duration_ratio"]
                      and quality and mos_delta >= -self.config["maximum_dnsmos_drop"])
            reports.append({"variant": variant, "pairs": len(pairs), "critical_pairs": len(critical),
                            "fact_gain": fact_gain, "wer_delta": wer_delta, "duration_ratio": ratio,
                            "dnsmos_ovrl_delta": mos_delta, "screen_pass": bool(passes)})
        return pd.DataFrame(reports)

    def select(self, conditions, listening_review):
        destination = self.root / "selection.json"
        if destination.exists():
            return json.loads(destination.read_text())
        challenge = json.loads((self.root / "challenge.json").read_text())
        if conditions != challenge["conditions"]:
            raise ValueError("Selection must use the previously frozen baseline challenge")
        dev = self.all_results("dev")
        validate_challenges(dev, conditions, self.config["replicates"])
        table = self.comparisons(dev, conditions)
        table.to_csv(self.root / "development_comparisons.csv", index=False)
        passing = table[table.screen_pass].sort_values(["fact_gain", "wer_delta"], ascending=[False, True])
        for record in passing.to_dict("records"):
            review = listening_review.get(record["variant"], {})
            if review.get("facts_preserved") and review.get("quality_acceptable"):
                decision = {**record, "conditions": conditions, "listening_review": review,
                            "fingerprint": self.fingerprint, "frozen_utc": datetime.now(timezone.utc).isoformat()}
                save_json(destination, decision)
                return decision
        raise ValueError("No candidate passes the metrics AND listening review; report no winner")
