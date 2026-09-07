# %% Cell 1 - Mount Google Drive for persistent data, models and results.
# Copy each marked section into a separate Colab cell. Three blank lines separate cells.
from pathlib import Path
import subprocess
import sys
from google.colab import drive

drive.mount("/content/drive")
REPO = Path("/content/DataForge-delivery")
WORK = Path("/content/drive/MyDrive/DataForge")
WORK.mkdir(parents=True, exist_ok=True)
print("Persistent experiment folder:", WORK)



# %% Cell 2 - Load the GitHub branch into the Colab runtime.
# Git branches are cloned, while Drive is mounted in Cell 1.
BRANCH = "noise-conditioned-ab"
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
    raise ValueError("Project files missing; clone the branch or extract the source ZIP into /content/DataForge-delivery")
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



# %% Cell 4 - Copy the completed Noise-Masking outputs into this branch.
import json
from dataforge.handoff import copy_run, copy_grid_results
SOURCE_NOISE_RUN = WORK / "noise_masking/outputs/REPLACE_WITH_RUN_ID"
COPIED_BASELINE = copy_run(SOURCE_NOISE_RUN, REPO / "inputs/noise_masking", for_delivery=True)
print("Copied baseline inputs:", COPIED_BASELINE)
# Optional: copy Grid Analysis conclusions for this same development baseline.
GRID_RESULTS = None  # e.g. WORK / "grid_analysis/outputs/RUN_ID/SESSION/results"
COPIED_GRID = None
if GRID_RESULTS is not None:
    source_id = json.loads((COPIED_BASELINE / "handoff.json").read_text())["run_id"]
    COPIED_GRID = copy_grid_results(GRID_RESULTS, REPO / "inputs/grid_analysis", source_id)
    print("Copied grid conclusions:", COPIED_GRID)



# %% Cell 5 - Import the frozen baseline; this cell performs no synthesis or ASR.
from google.colab import userdata
from IPython.display import Audio, display
import pandas as pd
from dataforge.delivery import start_delivery
from dataforge.experiment import validate_catalog, validate_challenges, noise_failure_evidence, save_json
RIME_API_KEY = userdata.get("RIME_API_KEY")
experiment = start_delivery(COPIED_BASELINE, WORK / "delivery_ab/outputs")
config, corpus, noises = experiment.config, experiment.corpus, experiment.noises
# The original noise datasets and downloaded evaluator models stay in shared Drive.
if not Path(config["asr_local_path"]).is_dir() or not Path(config["dnsmos_model_path"]).is_file():
    raise ValueError("Retain the Noise-Masking evaluator downloads at their original Drive paths")
save_json(experiment.root / "catalog_check.json", validate_catalog(config))
baseline = experiment.all_results("dev")
recurrent = noise_failure_evidence(baseline, config["replicates"])
display(recurrent.groupby("condition").text_id.nunique().rename("recurrent_texts"))
if COPIED_GRID is not None:
    display(pd.read_csv(COPIED_GRID / "development_challenge_cases.csv"))
print("Baseline imported without rerunning it; A/B outputs:", experiment.root)



# %% Cell 6 - Freeze one or two challenge conditions from repeatable baseline failures.
# Enter conditions shown in Cell 5 with at least two recurrent texts.
CHALLENGE_CONDITIONS = []
# If no noisy failure repeats, stop here; baseline diagnostics are already saved.
# This branch preserves the imported grid/configuration. Use Noise Masking for a new baseline.
challenge_evidence = validate_challenges(baseline, CHALLENGE_CONDITIONS, config["replicates"])
challenge_evidence.to_csv(experiment.root / "challenge_evidence.csv", index=False)
challenge_path = experiment.root / "challenge.json"
if challenge_path.exists():
    assert json.loads(challenge_path.read_text())["conditions"] == CHALLENGE_CONDITIONS, "Challenge already frozen"
else:
    save_json(challenge_path, {"conditions": CHALLENGE_CONDITIONS, "basis": "development baseline only"})
print("Frozen challenge:", CHALLENGE_CONDITIONS)



# %% Cell 7 - A/B development: one intervention per variant, model and voice fixed.
# 'clauses' = short fact clauses; 'repeat' = repeat reference code; 'slow' = timeScaleFactor 1.1.
# These are explicit, auditable synthetic variants. No upstream LLM service is required.
# General texts are unchanged for clauses/repeat and act as negative controls.
variants = experiment.run("dev", ["clauses", "repeat", "slow"], RIME_API_KEY)
development = experiment.all_results("dev")
comparison = experiment.comparisons(development, CHALLENGE_CONDITIONS)
display(comparison)



# %% Cell 8 - Listen to matched pairs and verify facts, contradictions, and naturalness.
REVIEW_TEXT_ID = next(x["id"] for x in corpus if x["split"] == "dev" and x["facts"])
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



# %% Cell 9 - Freeze the winning candidate before accessing held-out results.
# Populate LISTENING_REVIEW in Cell 8. A no-winner result is valid evidence.
selection = experiment.select(CHALLENGE_CONDITIONS, LISTENING_REVIEW)
print("Frozen candidate:", selection["variant"])



# %% Cell 10 - One held-out validation; resumes use the same cached outputs and candidate.
validation = experiment.run("heldout", ["baseline", selection["variant"]], RIME_API_KEY)
validation_comparison = experiment.comparisons(validation, selection["conditions"])
validation_comparison.to_csv(experiment.root / "heldout_comparison.csv", index=False)
display(validation_comparison)
print("Do not tune the candidate or thresholds on this held-out result. A failure means no validated improvement.")



# %% Cell 11 - Export metrics, plots, and a truthful evidence status.
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
    "scope": f"{len(noises)} noise files, fixed text split, simulated 8 kHz PCMU channel; see evidence_scope.json",
    "limitations": "ASR fact recovery is a lexical proxy; no human comprehension study or general noise policy",
})
print("Saved evidence in:", experiment.root)
print("Metric screen passed:", passed, "— verify held-out facts and naturalness before making a final claim.")
validation[validation.fact_count > 0][review_columns].to_csv(
    experiment.root / "heldout_listening_queue.csv", index=False)
