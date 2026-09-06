# %% Cell 1 - Mount Drive and clone the experiment branch.
# Copy each marked section into a separate Colab cell. Three blank lines separate cells.
# If the branch has not been pushed, upload a zip of this workspace to Colab instead.
from pathlib import Path
import subprocess
import sys
from google.colab import drive

drive.mount("/content/drive")
REPO = Path("/content/DataForge")
BRANCH = "codex/noise-conditioned-ab"
if not REPO.exists():
    subprocess.run(["git", "clone", "--branch", BRANCH, "https://github.com/Drazr/DataForge.git", str(REPO)], check=True)
if (REPO / ".git").exists():
    active_branch = subprocess.check_output(["git", "-C", str(REPO), "branch", "--show-current"], text=True).strip()
    assert active_branch == BRANCH, f"Expected {BRANCH}, found {active_branch}; choose the correct checkout"
    print(active_branch)
else:
    print("Using uploaded source archive; retain its GitHub commit separately for evidence.")
WORK = Path("/content/drive/MyDrive/DataForge")
WORK.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))



# %% Cell 2 - Install dependencies. Use a fresh runtime if Colab asks for a restart.
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(REPO / "requirements-colab.txt")], check=True)
subprocess.run(["apt-get", "-qq", "update"], check=True)
subprocess.run(["apt-get", "-qq", "install", "-y", "ffmpeg"], check=True)
print("Dependencies installed. If a runtime restart is requested, restart and rerun Cell 1, then continue at Cell 3.")



# %% Cell 3 - Configuration and secret. No TTS charges occur in this cell.
import json
import os
from google.colab import userdata
from IPython.display import Audio, display
from dataforge.experiment import Experiment, load_corpus, save_json, validate_catalog
from dataforge.downloads import download_musan, prepare_models

RIME_API_KEY = userdata.get("RIME_API_KEY")
config = json.loads((REPO / "experiment.json").read_text())
# Choose these before Cell 6 freezes the run. Extra SNR points increase scoring time.
# For a finer initial sweep, use [10, 7.5, 5, 2.5, 0]. Keep held-out texts untouched.
config["snrs_db"] = [10, 5, 0]
# CPU/int8 is portable. For a supported Colab GPU, set both values before models load:
# config["asr_device"] = "cuda"
# config["asr_compute_type"] = "float16"
catalog_check = validate_catalog(config)
corpus = load_corpus(REPO / "fixtures/corpus.json")
print("Catalog verified; 30 original synthetic texts, split 21 development / 9 held-out.")
print("Synthesis budget:", config["max_request_characters"], "characters; attempts count even if they fail.")



# %% Cell 4 - Download MUSAN, or use an existing copy. Large download: about 11 GB.
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



# %% Cell 5 - Choose and listen to two noise files before approving their labels.
# Replace paths with real selections from Cell 4; read MUSAN source metadata.
NOISE_PATH = ""  # a traffic or machinery WAV selected from MUSAN
SPEECH_PATH = ""  # one competing-speaker WAV; do not label one speaker as babble
NOISE_OFFSET_S = 0
SPEECH_OFFSET_S = 0
if not NOISE_PATH or not SPEECH_PATH:
    raise ValueError("Choose NOISE_PATH and SPEECH_PATH from the downloaded files, then rerun this cell")
for selected in (NOISE_PATH, SPEECH_PATH):
    display(Audio(filename=selected))



# %% Cell 6 - Approve sources, resolve model versions, and initialize this experiment.
NOISE_LABELS_VERIFIED = False  # set True after listening and checking source descriptions
if not NOISE_LABELS_VERIFIED:
    raise ValueError("Confirm the selected sounds and labels by setting NOISE_LABELS_VERIFIED=True")
noises = [
    {"id": "competing_speech", "path": SPEECH_PATH, "offset_s": SPEECH_OFFSET_S,
     "kind": "competing_speech", "verified_by_listening": True, "source": "https://www.openslr.org/17/", "license": "CC BY 4.0"},
    {"id": "environment", "path": NOISE_PATH, "offset_s": NOISE_OFFSET_S,
     "kind": "traffic_or_machinery", "verified_by_listening": True, "source": "https://www.openslr.org/17/", "license": "CC BY 4.0"},
]
save_json(WORK / "noise_manifest.json", noises)
config = prepare_models(config, WORK / "models")
experiment = Experiment(config, corpus, noises, WORK / "outputs")
save_json(experiment.root / "catalog_check.json", catalog_check)
(experiment.root / "pip-freeze.txt").write_text(subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True))
revision = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True) if (REPO / ".git").exists() else "source archive; commit not available"
(experiment.root / "git-revision.txt").write_text(revision)
(experiment.root / "ffmpeg-version.txt").write_text(subprocess.check_output(["ffmpeg", "-version"], text=True))
print("Run directory:", experiment.root)



# %% Cell 7 - Baseline preflight: one billed Rime request, then listen for correct facts.
item = next(x for x in corpus if x["id"] == "critical_01")
sample, sample_metadata = experiment.synthesize(item, "baseline", 0, RIME_API_KEY)
display(Audio(filename=str(sample)))
print(item["text"])
print("Duration:", sample_metadata["duration_s"], "seconds; raw peak:", sample_metadata["raw_peak"])



# %% Cell 8 - Development baseline and diagnostics (294 scores with the default grid).
# New TTS calls are billed; completed audio and scores are cached in Drive for resumes.
PREFLIGHT_AUDIO_VERIFIED = False  # True after the voice, words, and completion sound correct
if not PREFLIGHT_AUDIO_VERIFIED:
    raise ValueError("Verify the preflight audio before generating the development corpus")
baseline = experiment.run("dev", ["baseline"], RIME_API_KEY)
display(baseline.groupby("condition")[["wer", "fact_recovery", "dnsmos_ovrl"]].mean())
failures = baseline[(baseline.fact_count > 0) & (baseline.fact_recovery < 1)]
display(failures[["text_id", "replicate", "condition", "reference_text", "transcript", "fact_recovery"]])
from dataforge.reporting import export_baseline
baseline_summary, fact_failures = export_baseline(baseline, experiment.root)
display(baseline_summary)
display(fact_failures)
print("Baseline CSVs and SNR plots saved before any intervention selection:", experiment.root)
print("Listen to clean and noisy versions of failed texts; ASR errors alone do not prove human misunderstanding.")



# %% Cell 9 - Freeze one or two challenge conditions from repeatable baseline failures.
# Enter labels shown in Cell 8, e.g. ["environment_5dB", "competing_speech_0dB"].
CHALLENGE_CONDITIONS = []
# If no noisy failure repeats, stop here; baseline diagnostics are already saved.
# A finer follow-up grid belongs in a separately recorded development run (Cell 3),
# before candidate selection. It does not establish a universal SNR threshold.
if not CHALLENGE_CONDITIONS or len(CHALLENGE_CONDITIONS) > 2:
    raise ValueError("Choose one or two development failure conditions; if none repeat, report no demonstrated failure")
for condition in CHALLENGE_CONDITIONS:
    failed = failures[failures.condition == condition]
    if failed.text_id.nunique() < 2 or failed.replicate.nunique() < config["replicates"]:
        raise ValueError("Challenge must fail on multiple texts and both synthesis repeats")
challenge_path = experiment.root / "challenge.json"
if challenge_path.exists():
    assert json.loads(challenge_path.read_text())["conditions"] == CHALLENGE_CONDITIONS, "Challenge already frozen"
else:
    save_json(challenge_path, {"conditions": CHALLENGE_CONDITIONS, "basis": "development baseline only"})
print("Frozen challenge:", CHALLENGE_CONDITIONS)



# %% Cell 10 - A/B development: one intervention per variant, model and voice fixed.
# 'clauses' = short fact clauses; 'repeat' = repeat reference code; 'slow' = timeScaleFactor 1.1.
# These are explicit, auditable synthetic variants. No upstream LLM service is required.
# General texts are unchanged for clauses/repeat and act as negative controls.
variants = experiment.run("dev", ["clauses", "repeat", "slow"], RIME_API_KEY)
development = experiment.all_results("dev")
comparison = experiment.comparisons(development, CHALLENGE_CONDITIONS)
display(comparison)



# %% Cell 11 - Listen to matched pairs and verify facts, contradictions, and naturalness.
REVIEW_TEXT_ID = "critical_01"
for variant in ("baseline", "clauses", "repeat", "slow"):
    clips = development[(development.text_id == REVIEW_TEXT_ID) & (development.variant == variant)
                        & (development.condition == CHALLENGE_CONDITIONS[0]) & (development.replicate == 0)]
    if not clips.empty:
        print(variant, clips.iloc[0].reference_text, "ASR:", clips.iloc[0].transcript)
        display(Audio(filename=clips.iloc[0].audio_path))
# Repeat with all development critical texts / challenge conditions before approval.
# Also listen to the saved clean conditions. ASR matching alone cannot establish comprehension.
review_columns = ["text_id", "variant", "replicate", "condition", "reference_text", "transcript", "audio_path"]
development[(development.fact_count > 0) &
            development.condition.isin(["clean", *CHALLENGE_CONDITIONS])][review_columns].to_csv(
                experiment.root / "development_listening_queue.csv", index=False)
LISTENING_REVIEW = {
    "clauses": {"facts_preserved": False, "quality_acceptable": False, "notes": ""},
    "repeat": {"facts_preserved": False, "quality_acceptable": False, "notes": ""},
    "slow": {"facts_preserved": False, "quality_acceptable": False, "notes": ""},
}



# %% Cell 12 - Freeze the winning candidate before accessing held-out results.
# Populate LISTENING_REVIEW in Cell 11. A no-winner result is valid evidence.
selection = experiment.select(CHALLENGE_CONDITIONS, LISTENING_REVIEW)
print("Frozen candidate:", selection["variant"])



# %% Cell 13 - One held-out validation; resumes use the same cached outputs and candidate.
validation = experiment.run("heldout", ["baseline", selection["variant"]], RIME_API_KEY)
validation_comparison = experiment.comparisons(validation, selection["conditions"])
validation_comparison.to_csv(experiment.root / "heldout_comparison.csv", index=False)
display(validation_comparison)
print("Do not tune the candidate or thresholds on this held-out result. A failure means no validated improvement.")



# %% Cell 14 - Export metrics, plots, and a truthful evidence status.
import matplotlib.pyplot as plt
import pandas as pd

all_rows = pd.concat([experiment.all_results("dev"), experiment.all_results("heldout")], ignore_index=True)
all_rows.to_csv(experiment.root / "results.csv", index=False)
grouped = all_rows.groupby(["split", "variant", "condition"], dropna=False).agg(
    clips=("clip_id", "count"), wer=("wer", "mean"), fact_recovery=("fact_recovery", "mean"),
    duration_s=("duration_s", "mean"), dnsmos_ovrl=("dnsmos_ovrl", "mean"))
grouped.to_csv(experiment.root / "condition_summary.csv")
for metric in ("wer", "fact_recovery", "dnsmos_ovrl"):
    chart = validation.groupby(["condition", "variant"])[metric].mean().unstack()
    chart.plot.bar(figsize=(11, 4), ylabel=metric, title=f"Held-out {metric} (condition means)")
    plt.tight_layout()
    plt.savefig(experiment.root / f"{metric}.png", dpi=150)
    plt.show()
passed = bool(validation_comparison.iloc[0].screen_pass)
save_json(experiment.root / "evidence_status.json", {
    "candidate": selection["variant"], "heldout_metric_screen_pass": passed,
    "human_heldout_review": "pending", "real_phone_validation": "not run",
    "scope": "two noise files, fixed text split, simulated 8 kHz PCMU channel",
    "limitations": "ASR fact recovery is a lexical proxy; no human comprehension study or general noise policy",
})
print("Saved evidence in:", experiment.root)
print("Metric screen passed:", passed, "— verify held-out facts and naturalness before making a final claim.")
validation[validation.fact_count > 0][review_columns].to_csv(
    experiment.root / "heldout_listening_queue.csv", index=False)



# %% Cell 15 - Optional real HTTP streaming probe (extra billed calls, no phone account needed).
RUN_STREAMING_PROBE = False
if RUN_STREAMING_PROBE:
    from datetime import datetime, timezone
    stream_output = WORK / "outputs" / ("stream-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    environment = dict(os.environ)
    environment["RIME_API_KEY"] = RIME_API_KEY
    subprocess.run([sys.executable, str(REPO / "scripts/stream_probe.py"),
                    "--config", str(REPO / "experiment.json"), "--output", str(stream_output)],
                   env=environment, check=True)
    del environment
    print("Probe artifacts:", stream_output)
    print("Decode PCMU with: ffmpeg -f mulaw -ar 8000 -ac 1 -i INPUT.ulaw OUTPUT.wav")
