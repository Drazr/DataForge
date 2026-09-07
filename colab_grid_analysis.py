# %% Cell 1 - Mount Drive and locate the completed baseline exports.
# Copy each marked section into its own cell. Exactly three blank lines separate cells.
# Reuse the Noise Masking or Noise-Conditioned Delivery A/B run folder directly.
# colab_noise_ab.py Cell 9 exports everything needed; no A/B winner is required.
from pathlib import Path
import subprocess
import sys
from google.colab import drive

drive.mount("/content/drive")
REPO = Path("/content/DataForge-grid")
RUN_DIR = Path("/content/drive/MyDrive/DataForge/outputs/REPLACE_WITH_RUN_ID")
if not RUN_DIR.is_dir():
    raise ValueError("Set RUN_DIR to the Noise Masking or Noise-Conditioned A/B folder containing the baseline exports")
print("Evidence folder:", RUN_DIR)
print("Use a separate analysis notebook; the completed baseline is sufficient.")



# %% Cell 2 - Load the analysis branch (or use an uploaded source archive).
# The branch must be committed and pushed before cloning it from GitHub.
BRANCH = "codex/grid-breakpoint-analysis"
REPO_URL = "https://github.com/Drazr/DataForge.git"
if not REPO.exists():
    subprocess.run(["git", "clone", "--single-branch", "--branch", BRANCH, REPO_URL, str(REPO)], check=True)
if (REPO / ".git").is_dir():
    active = subprocess.check_output(["git", "-C", str(REPO), "branch", "--show-current"], text=True).strip()
    if active != BRANCH:
        raise ValueError(f"Expected {BRANCH}, found {active}; use a separate checkout")
    REVISION = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    print("Commit:", REVISION, "(existing checkouts are not automatically updated)")
else:
    REVISION = "uploaded source archive; retain original commit separately"
if not (REPO / "dataforge/grid_analysis.py").is_file():
    raise ValueError("Missing analysis files; clone the analysis branch or extract its source archive into REPO")
sys.path.insert(0, str(REPO))



# %% Cell 3 - Install lightweight analysis dependencies on a CPU runtime.
if sys.version_info[:2] not in {(3, 11), (3, 12)}:
    raise RuntimeError("The dependency pins target Python 3.11/3.12; choose a compatible runtime")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(REPO / "requirements-grid.txt")], check=True)
print("If Colab requests a restart, restart and rerun Cells 1-2, then continue at Cell 4.")



# %% Cell 4 - Freeze analysis settings BEFORE reviewing the grid.
import copy
import json
from datetime import datetime, timezone
from IPython.display import Audio, Image, display
from dataforge.grid_analysis import load_evidence, load_performance_grid, run_analysis, validate_settings, write_json

SETTINGS = json.loads((REPO / "grid_analysis.json").read_text())
SETTINGS["input_file"] = "baseline_results.csv"  # Preferred; available immediately after the A/B baseline finishes.
# Later, choose results.csv and ONE split/variant below per analysis session.
# Never concatenate it with baseline_results.csv or dev_baseline.csv.
SETTINGS["split"] = "dev"  # heldout is reporting only; no challenge selection.
SETTINGS["variant"] = "baseline"
SETTINGS["acceptance"] = {
    "maximum_wer": None,              # User-selected absolute limit; fractional WER, e.g. 0.1 = 10%.
    "minimum_fact_recovery": None,    # User-selected absolute limit in [0, 1].
    "rationale": "",                  # Required when either limit is set.
    "established_before_review": False,
}
# With both limits None, analysis proceeds and reports deterioration only.
# Recurrence defaults: >=2 texts, >=50% eligible texts, every configured repeat,
# at least 2 repeats, positive mean deterioration, and a complete planned interval.
# Change these pilot choices BEFORE reviewing evidence; zero delta is a direction
# test, not a minimum practically important effect. See GRID_ANALYSIS_RUNBOOK.md.
# Optional old-to-new audio-root mappings after moving the run directory:
# SETTINGS["audio_path_remap"] = {"/old/DataForge/outputs": "/content/drive/MyDrive/DataForge/outputs"}
validate_settings(SETTINGS)
FROZEN_SETTINGS = copy.deepcopy(SETTINGS)
ANALYSIS_ROOT = RUN_DIR / "grid_analysis"
SESSION = ANALYSIS_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
SESSION.mkdir(parents=True, exist_ok=False)
write_json(SESSION / "settings_before_review.json", FROZEN_SETTINGS)
(SESSION / "git-revision.txt").write_text(REVISION)
print("Saved settings:", SESSION)



# %% Cell 5 - Verify the producer files and review the EXISTING performance grid.
rows, manifest, scope, missing, checks = load_evidence(RUN_DIR, FROZEN_SETTINGS)
print("Rows:", checks["selected_rows"], "Expected:", checks["expected_rows"])
print("Scope:", checks["scope_source"])
display(missing)
grid_preview, grid_source = load_performance_grid(RUN_DIR, rows, FROZEN_SETTINGS, checks["warnings"])
display(grid_preview)
print("Performance grid:", grid_source)
if grid_source == "baseline_condition_summary.csv":
    # Only these three existing metric plots are used. DNSMOS is excluded.
    for metric in ("wer", "fact_recovery", "estoi"):
        plot = RUN_DIR / f"baseline_{metric}.png"
        if plot.is_file():
            display(Image(filename=str(plot)))
    print("Reusing the producer grid and available plots. Paired calculations use the verified per-clip rows.")
else:
    print("Using the selected-row grid; baseline plots are not shown without a matching baseline summary.")
for warning in checks["warnings"]:
    print(warning)



# %% Cell 6 - Compute paired changes, uncertainty, and configured limit crossings.
if SETTINGS != FROZEN_SETTINGS:
    raise ValueError("Settings changed after freezing; record a new analysis session in Cell 4")
OUTPUT = SESSION / "results"
analysis = run_analysis(RUN_DIR, FROZEN_SETTINGS, OUTPUT)
display(analysis["grid"])
display(analysis["intervals"])
for metric in ("wer", "fact_recovery", "estoi"):
    display(Image(filename=str(OUTPUT / f"adjacent_{metric}.png")))
print((OUTPUT / "REPORT.md").read_text())
# Outputs are immutable per session. To rerun, start a new session at Cell 4.



# %% Cell 7 - Review linked development challenge candidates and retain exports.
cases = analysis["challenges"]
display(cases)
# Optional listening only: no new synthesis, scoring, or intervention selection.
PLAY_FIRST_PAIR = False
if PLAY_FIRST_PAIR and not cases.empty:
    selected = cases.iloc[0]
    for label, column in (("Clean", "resolved_clean_audio_path"), ("Noisy", "resolved_audio_path")):
        print(label, selected.text_id, selected.condition, selected.fact_id)
        if Path(selected[column]).is_file():
            display(Audio(filename=selected[column]))
        else:
            print("Audio missing:", selected[column], "-- configure audio_path_remap in Cell 4")
print("Persistent outputs:", OUTPUT)
print("Hand development_challenge_cases.csv to the separate delivery A/B workflow for review.")
print("No A/B challenge, candidate, or acceptance limit was selected automatically.")
