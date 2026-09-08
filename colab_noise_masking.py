# %% Cell 1 - Mount Google Drive for persistent data, models and results.
# Copy each marked section into a separate Colab cell. Three blank lines separate cells.
from pathlib import Path
import subprocess
import sys
from google.colab import drive

drive.mount("/content/drive")
REPO = Path("/content/DataForge-noise")
WORK = Path("/content/drive/MyDrive/DataForge")
WORK.mkdir(parents=True, exist_ok=True)
print("Persistent experiment folder:", WORK)



# %% Cell 2 - Load the GitHub branch into the Colab runtime.
# Git branches are cloned, while Drive is mounted in Cell 1.
BRANCH = "noise-masking-test"
REPO_URL = "https://github.com/Drazr/DataForge.git"
if not REPO.exists():
    subprocess.run(["git", "clone", "--single-branch", "--branch", BRANCH, REPO_URL, str(REPO)], check=True)
if (REPO / ".git").exists():
    active_branch = subprocess.check_output(["git", "-C", str(REPO), "branch", "--show-current"], text=True).strip()
    if active_branch != BRANCH:
        raise ValueError(f"Expected {BRANCH}, found {active_branch}; choose the correct checkout")
    print("Branch:", active_branch, "Commit:", subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip())
    print("Existing checkouts stay at this commit for reproducibility; use a fresh runtime for updated branch code.")
else:
    print("Using uploaded source archive; retain its GitHub commit separately for evidence.")
if not (REPO / "experiment.json").is_file():
    raise ValueError("Project files missing; clone the branch or extract the source ZIP into /content/DataForge-noise")
sys.path.insert(0, str(REPO))



# %% Cell 3 - Install dependencies for Python 3.11, 3.12 or 3.13.
if sys.version_info[:2] not in {(3, 11), (3, 12), (3, 13)}:
    raise RuntimeError("Use Python 3.11, 3.12 or 3.13 for this workflow")
requirements = (REPO / "requirements-colab.txt").read_text()
if sys.version_info[:2] == (3, 13):
    replacements = {
        "numpy": "numpy>=2.2,<3", "scipy": "scipy>=1.15,<2",
        "pandas": "pandas>=2.2.3,<3", "matplotlib": "matplotlib>=3.10,<4",
        "faster-whisper": "faster-whisper>=1.2.1,<2",
        "librosa": "librosa>=0.11,<1", "onnxruntime": "onnxruntime>=1.22.1,<2",
    }
    requirements = "\n".join(
        replacements.get(line.split("==", 1)[0].strip(), line)
        for line in requirements.splitlines()
    ) + "\nnumba>=0.61.2\nctranslate2>=4.6,<5\n"
runtime_requirements = REPO / "requirements-colab-runtime.txt"
runtime_requirements.write_text(requirements + "\n")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--prefer-binary",
                "-r", str(runtime_requirements)], check=True)
subprocess.run(["apt-get", "-qq", "update"], check=True)
subprocess.run(["apt-get", "-qq", "install", "-y", "ffmpeg"], check=True)
print("Restart the Colab session after installation to unload old packages. "
      "Then rerun Cells 1-2 and continue at Cell 4; skip Cell 3.")



# %% Cell 4 - Configuration and secret. No TTS charges occur in this cell.
import json
import os
from google.colab import userdata
from IPython.display import Audio, display
from dataforge.experiment import (Experiment, load_corpus, save_json, validate_catalog,
                                  validate_challenges, noise_failure_evidence,
                                  audio_read, level_active, phone_roundtrip, fact_score)
from dataforge.downloads import download_musan, prepare_models

RIME_API_KEY = userdata.get("RIME_API_KEY")
config = json.loads((REPO / "experiment.json").read_text())
# Choose before Cell 7 freezes the run. This profile is a separate, stronger
# development baseline: 0 dB retains comparability and -5 dB precommits a
# materially harsher condition. It never accesses held-out texts.
BASELINE_PROFILE = "stress_0_to_minus5"
BASELINE_PROFILES = {
    "standard_10_to_0": [10, 5, 0],
    "stress_0_to_minus5": [0, -5],
}
if BASELINE_PROFILE not in BASELINE_PROFILES:
    raise ValueError(f"Unknown baseline profile: {BASELINE_PROFILE}")
config["snrs_db"] = BASELINE_PROFILES[BASELINE_PROFILE]
config["baseline_profile"] = BASELINE_PROFILE

# The stress profile evaluates 21 development texts x 2 repeats x 5 conditions.
# Select Runtime > Change runtime type > T4 GPU before using this profile.
GPU_REQUIRED = True
if GPU_REQUIRED:
    try:
        gpu = subprocess.run(["nvidia-smi", "-L"], check=True, capture_output=True, text=True).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise RuntimeError("Select a Colab T4 GPU, restart the session, and rerun Cells 1-4") from error
    config["asr_device"] = "cuda"
    config["asr_compute_type"] = "float16"
    print("GPU evaluator:", gpu)

conditions = 1 + 2 * len(config["snrs_db"])
planned_scores = sum(x["split"] == "dev" for x in json.loads((REPO / "fixtures/corpus.json").read_text())) * config["replicates"] * conditions
print(f"Baseline profile: {BASELINE_PROFILE}; planned development scores: {planned_scores}")
catalog_check = validate_catalog(config)
CORPUS_PATH = REPO / "fixtures/corpus.json"  # Replace with a larger, pre-split corpus before any run.
corpus = load_corpus(CORPUS_PATH)
print("Catalog verified; texts by split:", {s: sum(x["split"] == s for x in corpus) for s in ("dev", "heldout")})
print("Synthesis budget:", config["max_request_characters"], "characters; attempts count even if they fail.")



# %% Cell 5 - Download MUSAN, or use an existing copy. Large download: about 11 GB.
# Set DOWNLOAD_MUSAN=True only when ready. Keep the archive in Colab temporary storage.
# Retains environmental noise, four speech files, and licensing/description metadata.
DOWNLOAD_MUSAN = False
if DOWNLOAD_MUSAN:
    musan = download_musan(WORK / "data", Path("/content/musan-download"))
else:
    musan = WORK / "data/musan"
noise_files = sorted(musan.glob("noise/**/*.wav"))
speech_files = sorted(musan.glob("speech/**/*.wav"))
print("Environmental clips:", len(noise_files), "Speech clips:", len(speech_files))
print("Inspect descriptions in these files:", list(musan.glob("noise/**/ANNOTATIONS")) + list(musan.glob("noise/**/README*")))
print("First noise paths:", *noise_files[:10], sep="\n")
print("Speech paths:", *speech_files, sep="\n")
if not noise_files or not speech_files:
    raise ValueError("No complete noise dataset found. Enable DOWNLOAD_MUSAN or place an existing MUSAN copy at the printed path: " + str(musan))



# %% Cell 6 - Select and listen to noise candidates before verifying labels.
import re
descriptions = {}
for metadata in sorted(musan.glob("noise/**/ANNOTATIONS")):
    for line in metadata.read_text(errors="replace").splitlines():
        match = re.search(r"noise-[\w-]+", line)
        if match:
            descriptions[match.group(0).removesuffix(".wav")] = line.strip()
keywords = re.compile(
    r"\b(traffic|trucks?|engines?|machinery|motor|tractor|construction|highway|motorway)\b",
    re.IGNORECASE,
)
candidates = [path for path in noise_files if keywords.search(descriptions.get(path.stem, ""))]
# Change these indices and rerun to audition other recordings.
NOISE_INDEX, SPEECH_INDEX = 0, 0
if not noise_files or not speech_files:
    raise ValueError("Run Cell 5 to download or locate MUSAN first")
NOISE_PATH = str((candidates or noise_files)[NOISE_INDEX])
SPEECH_PATH = str(speech_files[SPEECH_INDEX])
NOISE_OFFSET_S, SPEECH_OFFSET_S = 0, 0
NOISE_LABELS_VERIFIED = False
print("Traffic/machinery metadata matches:", len(candidates))
if not candidates:
    print("No metadata match: identify the selected noise manually before approving it.")
for label, selected in (("Environmental candidate", NOISE_PATH), ("Competing speech", SPEECH_PATH)):
    print(label, selected)
    print("Metadata:", descriptions.get(Path(selected).stem, "Not indexed here"))
    display(Audio(filename=selected))
print("Verify traffic/machinery and a competing speaker by listening and reading metadata, "
      "then set NOISE_LABELS_VERIFIED=True in Cell 7.")



# %% Cell 7 - Approve sources, resolve model versions, and initialize this experiment.
NOISE_LABELS_VERIFIED = False  # set True after listening and checking source descriptions
if not NOISE_LABELS_VERIFIED:
    raise ValueError("Confirm the selected sounds and labels by setting NOISE_LABELS_VERIFIED=True")
noises = [
    {"id": "competing_speech", "path": SPEECH_PATH, "offset_s": SPEECH_OFFSET_S,
     "kind": "competing_speech", "verified_by_listening": True, "source": "https://www.openslr.org/17/", "license": "CC BY 4.0"},
    {"id": "environment", "path": NOISE_PATH, "offset_s": NOISE_OFFSET_S,
     "kind": "traffic_or_machinery", "verified_by_listening": True, "source": "https://www.openslr.org/17/", "license": "CC BY 4.0"},
]
# Optional independent recordings for a broader experiment, chosen before scoring.
# Each entry needs id, path, offset_s, kind, source, license, verified_by_listening.
EXTRA_NOISES = []
noises.extend(EXTRA_NOISES)
save_json(WORK / "noise_manifest.json", noises)
config = prepare_models(config, WORK / "models")
experiment = Experiment(config, corpus, noises, WORK / "noise_masking/outputs")
save_json(experiment.root / "catalog_check.json", catalog_check)
(experiment.root / "pip-freeze.txt").write_text(subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True))
revision = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True) if (REPO / ".git").exists() else "source archive; commit not available"
(experiment.root / "git-revision.txt").write_text(revision)
(experiment.root / "ffmpeg-version.txt").write_text(subprocess.check_output(["ffmpeg", "-version"], text=True))
print("Run directory:", experiment.root)
print("Shared synthesis cache and cumulative request budget ledger:", experiment.audio_cache)
save_json(experiment.root / "evidence_scope.json", {
    "texts_by_split": {s: sum(x["split"] == s for x in corpus) for s in ("dev", "heldout")},
    "critical_texts_by_split": {s: sum(x["split"] == s and bool(x["facts"]) for x in corpus) for s in ("dev", "heldout")},
    "noise_sources": len(noises), "synthesis_repeats": config["replicates"], "snrs_db": config["snrs_db"],
    "evidence_level": "pilot; ASR lexical proxy, not established human comprehension",
})



# %% Cell 8 - Live preflight: one billed Rime request plus real ASR/DNSMOS/codec checks.
item = next(x for x in corpus if x["split"] == "dev" and x["facts"])
sample, sample_metadata = experiment.synthesize(item, "baseline", 0, RIME_API_KEY)
display(Audio(filename=str(sample)))
print(item["text"])
print("Duration:", sample_metadata["duration_s"], "seconds; raw peak:", sample_metadata["raw_peak"])
# Exercise the installed evaluation models before the full synthesis batch.
import soundfile as sf
speech, sr = audio_read(sample)
preflight_phone = level_active(phone_roundtrip(speech, sr), config["speech_rms_dbfs"])
preflight_path = experiment.root / "preflight_phone.wav"
sf.write(preflight_path, preflight_phone, 8000, subtype="FLOAT")
preflight_transcript = experiment.transcribe(preflight_path)
preflight_facts, preflight_details = fact_score(preflight_transcript, item["facts"])
preflight_quality = experiment.quality(preflight_phone, 8000)
save_json(experiment.root / "runtime_preflight.json", {
    "run_id": experiment.fingerprint, "text_id": item["id"], "audio_path": str(preflight_path),
    "transcript": preflight_transcript, "fact_recovery": preflight_facts,
    "fact_details": preflight_details, "runtime_models_executed": True, **preflight_quality,
})
display(Audio(filename=str(preflight_path)))
print("Phone ASR:", preflight_transcript, "Fact recovery:", preflight_facts, "Quality:", preflight_quality)



# %% Cell 9 - Development baseline and diagnostics (294 scores with the default grid).
# New TTS calls are billed; completed audio and scores are cached in Drive for resumes.
PREFLIGHT_AUDIO_VERIFIED = False  # True after the voice, words, and completion sound correct
if not PREFLIGHT_AUDIO_VERIFIED:
    raise ValueError("Verify the preflight audio before generating the development corpus")
baseline = experiment.run("dev", ["baseline"], RIME_API_KEY)
display(baseline.groupby("condition")[["wer", "fact_recovery", "dnsmos_ovrl"]].mean())
failures = baseline[(baseline.fact_count > 0) & (baseline.fact_recovery < 1)]
display(failures[["text_id", "replicate", "condition", "reference_text", "transcript", "fact_recovery"]])
from dataforge.reporting import export_baseline
baseline_summary, fact_failures = export_baseline(baseline, experiment.root, replicates=config["replicates"])
display(baseline_summary)
display(fact_failures)
print("Baseline CSVs and SNR plots saved before any intervention selection:", experiment.root)
print("Listen to clean and noisy versions of failed texts; ASR errors alone do not prove human misunderstanding.")
recurrent = noise_failure_evidence(baseline, config["replicates"])
print("Texts with the same fact recovered cleanly but lost in noise in every repeat:")
display(recurrent.groupby("condition").text_id.nunique().rename("recurrent_texts"))
print("Noise-Masking Test complete. Copy this run folder into the Grid or Delivery branch using its handoff cell.")



# %% Cell 10 - Review and rescore saved facts without new synthesis or ASR.
from pathlib import Path
import hashlib
import json
import zipfile

import pandas as pd
from google.colab import files
from IPython.display import Audio, display
from dataforge.experiment import noise_failure_evidence, fact_score
import re
import copy

_default_review_source = (experiment.root if "experiment" in globals()
                          else "/content/drive/MyDrive/DataForge/noise_masking/outputs/1f95820a36625efe")
SOURCE_RUN = Path(globals().get("BASELINE_REVIEW_SOURCE", _default_review_source))
# Set BASELINE_REVIEW_SOURCE only to review a different completed run.
manifest_path = SOURCE_RUN / "manifest.json"
manifest = json.loads(manifest_path.read_text())
run_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
records = [json.loads(path.read_text()) for path in sorted((SOURCE_RUN / "rows").glob("*.json"))]
records = [row for row in records if row["split"] == "dev" and row["variant"] == "baseline"]
baseline_review = pd.DataFrame(records)
conditions = ["clean"] + [
    f"{noise['id']}_{snr}dB"
    for noise in manifest["noise"] for snr in manifest["config"]["snrs_db"]
]
expected = {
    (item["id"], rep, condition)
    for item in manifest["corpus"] if item["split"] == "dev"
    for rep in range(manifest["config"]["replicates"])
    for condition in conditions
}
actual = [(row["text_id"], row["replicate"], row["condition"]) for row in records]
if (not records or len(actual) != len(set(actual)) or set(actual) != expected
        or any(row["run_id"] != run_id for row in records)):
    raise ValueError("Baseline is incomplete or does not match its frozen manifest.")

recurrent_review = noise_failure_evidence(baseline_review, manifest["config"]["replicates"])
counts = recurrent_review.groupby("condition").text_id.nunique().reindex(
    conditions[1:], fill_value=0
).rename("recurrent_texts")
eligible = counts[counts >= 2].index.tolist()
print(f"Verified {len(records)} baseline scores.")
display(counts.to_frame())
print("A/B-eligible conditions:", eligible or "None: each needs at least two recurrent texts.")


# This helper is identical to the updated scorer. Keeping it here also supports
# an existing Colab session that still has the original scoring module loaded.
def canonicalize_time(text):
    """Equate numeric clock formatting only when an explicit AM/PM is present."""
    pattern = (r"(?<![\w:.\-])(?P<hour>1[0-2]|0?[1-9])[:.\-]?\s*"
               r"(?P<minute>[0-5][0-9])\s*(?P<period>[ap])\.?\s*m\.?(?!\w)")
    return re.sub(pattern, lambda m: f"{int(m['hour'])}:{m['minute']} {m['period'].lower()}m",
                  text, flags=re.IGNORECASE)

rescored_records = copy.deepcopy(records)
facts_by_text = {item["id"]: item["facts"] for item in manifest["corpus"] if item["split"] == "dev"}
for row in rescored_records:
    details = {}
    for fact in facts_by_text[row["text_id"]]:
        prepared_fact = dict(fact)
        transcript = row["transcript"]
        if fact["id"] == "time":
            transcript = canonicalize_time(transcript)
            for key in ("aliases", "forbidden"):
                if key in fact:
                    prepared_fact[key] = [canonicalize_time(value) for value in fact[key]]
        _, scored = fact_score(transcript, [prepared_fact])
        details.update(scored)
    row["fact_details"] = details
    row["facts_recovered"] = sum(detail["recovered"] for detail in details.values())
    row["fact_recovery"] = row["facts_recovered"] / len(details) if details else None
    row["fact_scoring_revision"] = "time_format_v2"
rescored_frame = pd.DataFrame(rescored_records)
rescored_recurrent = noise_failure_evidence(rescored_frame, manifest["config"]["replicates"])
rescored_counts = rescored_recurrent.groupby("condition").text_id.nunique().reindex(
    conditions[1:], fill_value=0
).rename("rescored_recurrent_texts")
rescored_eligible = rescored_counts[rescored_counts >= 2].index.tolist()
changes = [
    {"clip_id": before["clip_id"], "fact_id": fact_id,
     "before": detail["recovered"], "after": after["fact_details"][fact_id]["recovered"],
     "transcript": before["transcript"]}
    for before, after in zip(records, rescored_records)
    for fact_id, detail in before["fact_details"].items()
    if detail != after["fact_details"][fact_id]
]
review_summary = {
    "source_run_id": run_id, "fact_scoring_revision": "time_format_v2",
    "scores": len(records), "changed_fact_decisions": len(changes),
    "eligible_conditions": rescored_eligible, "minimum_recurrent_texts": 2,
    "human_listening_review": "pending", "new_tts_calls": 0, "new_asr_calls": 0,
    "scope": "Derived fact-score review; original run, WER, ESTOI and DNSMOS unchanged. "
             "Not an A/B handoff run. Versioned migration is required before importing corrected scores.",
}
review_dir = SOURCE_RUN.parent / "reviews" / SOURCE_RUN.name / "time_format_v2"
review_dir.mkdir(parents=True, exist_ok=True)
(review_dir / "review_summary.json").write_text(json.dumps(review_summary, indent=2))
(review_dir / "rescored_rows.json").write_text(json.dumps(rescored_records, indent=2))
rescored_frame.to_csv(review_dir / "rescored_baseline_results.csv", index=False)
rescored_recurrent.to_csv(review_dir / "rescored_recurrence.csv", index=False)
pd.DataFrame(changes, columns=["clip_id", "fact_id", "before", "after", "transcript"]).to_csv(
    review_dir / "changed_fact_decisions.csv", index=False)
print("Time-format corrections:", len(changes))
display(pd.concat([counts, rescored_counts], axis=1))
print("Rescored A/B-eligible conditions:", rescored_eligible or "None; do not start A/B yet.")
print("Separate review reports:", review_dir)

# Include full, untruncated transcripts and all critical baseline audio for review.
critical = baseline_review[baseline_review.fact_count > 0].copy()
critical["bundle_audio_path"] = critical.clip_id.map(lambda value: f"clips/{value}.wav")
archive = Path(globals().get("BASELINE_REVIEW_EXPORT_DIR", "/content")) / f"baseline_review_{run_id[:16]}_time_v2.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
    for report_path in sorted(review_dir.iterdir()):
        if report_path.is_file():
            bundle.write(report_path, "review/" + report_path.name)
    bundle.write(manifest_path, "manifest.json")
    bundle.writestr("baseline_rows.json", json.dumps(records, indent=2))
    bundle.writestr("noise_failure_evidence.csv", recurrent_review.to_csv(index=False))
    bundle.writestr("recurrence_counts.csv", counts.to_csv())
    bundle.writestr("listening_queue.csv", critical.to_csv(index=False))
    bundle.writestr("eligibility.json", json.dumps({
        "run_id": run_id, "scores": len(records), "minimum_recurrent_texts": 2,
        "eligible_conditions": eligible, "human_listening_review": "pending",
    }, indent=2))
    for name in ("baseline_results.csv", "baseline_condition_summary.csv",
                 "baseline_fact_failures.csv", "evidence_scope.json",
                 "runtime_preflight.json", "git-revision.txt", "pip-freeze.txt"):
        path = SOURCE_RUN / name
        if path.is_file():
            bundle.write(path, name)
    for row in critical.to_dict("records"):
        path = SOURCE_RUN / "clips" / f"{row['clip_id']}.wav"
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["audio_sha256"]:
            raise ValueError(f"Audio does not match the saved score: {path}")
        bundle.write(path, row["bundle_audio_path"])

# Audition the recurrent failures against their matched clean recordings.
by_id = {row["clip_id"]: row for row in records}
for pair in recurrent_review.drop_duplicates(["clean_clip_id", "noisy_clip_id"]).to_dict("records"):
    print(f"\n{pair['text_id']} | repeat {pair['replicate']} | {pair['condition']}")
    for label, clip_id in (("Clean", pair["clean_clip_id"]), ("Noisy", pair["noisy_clip_id"])):
        row = by_id[clip_id]
        print(label, "reference:", row["reference_text"])
        print(label, "transcript:", row["transcript"])
        display(Audio(filename=str(SOURCE_RUN / "clips" / f"{clip_id}.wav")))

print("Review bundle:", archive)
print("Share this ZIP for transcript/scorer review; keep the original Drive run unchanged.")
files.download(str(archive))
