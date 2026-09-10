# %% Cell 1 - Mount Drive and select the completed v2 measurement run.
from pathlib import Path
import subprocess
import sys
from google.colab import drive

drive.mount("/content/drive")
WORK = Path("/content/drive/MyDrive/DataForge")
READY_RUN_ID = ""  # Leave blank when Drive contains exactly one completed v2 run.
root = WORK / "noise_grid_v2/outputs"
candidates = sorted(path.parent for path in root.glob("*/ready_for_grid.json"))
if READY_RUN_ID:
    SOURCE_RUN_DIR = root / READY_RUN_ID
elif len(candidates) == 1:
    SOURCE_RUN_DIR = candidates[0]
else:
    print("Completed candidates:", *candidates, sep="\n")
    raise ValueError("Set READY_RUN_ID to one completed v2 run")
print("Frozen producer run:", SOURCE_RUN_DIR)



# %% Cell 2 - Clone the same v2 branch into this CPU notebook.
REPO = Path("/content/DataForge-grid-v2-analysis")
BRANCH = "noise-grid-v2"
REPO_URL = "https://github.com/Drazr/DataForge.git"
if not REPO.exists():
    subprocess.run(["git", "clone", "--single-branch", "--branch", BRANCH, REPO_URL, str(REPO)], check=True)
if (REPO / ".git").exists():
    active = subprocess.check_output(["git", "-C", str(REPO), "branch", "--show-current"], text=True).strip()
    if active != BRANCH:
        raise ValueError(f"Expected {BRANCH}, found {active}; use a separate checkout")
    REVISION = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    print("Branch:", active, "Commit:", REVISION)
else:
    REVISION = "uploaded source archive; retain its source commit separately"
if not (REPO / "dataforge/grid_analysis.py").is_file():
    raise ValueError("Missing v2 grid-analysis code")
sys.path.insert(0, str(REPO))



# %% Cell 3 - Install lightweight CPU-only analysis dependencies.
if sys.version_info[:2] not in {(3, 11), (3, 12), (3, 13)}:
    raise RuntimeError("Use Python 3.11, 3.12 or 3.13")
requirements = (REPO / "requirements-grid.txt").read_text()
if sys.version_info[:2] == (3, 13):
    requirements = requirements.replace("numpy==1.26.4", "numpy>=2.2,<3")
    requirements = requirements.replace("pandas==2.2.3", "pandas>=2.2.3,<3")
    requirements = requirements.replace("matplotlib==3.9.4", "matplotlib>=3.10,<4")
runtime_requirements = REPO / "requirements-grid-runtime.txt"
runtime_requirements.write_text(requirements + "\n")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--prefer-binary",
                "-r", str(runtime_requirements)], check=True)
print("Analysis dependencies installed. CPU is sufficient; no GPU runtime is needed.")



# %% Cell 4 - Freeze the preregistered analysis settings before viewing results.
import copy
import json
from datetime import datetime, timezone
from dataforge.grid_analysis import load_evidence, load_performance_grid, run_analysis, validate_settings, write_json

ready = json.loads((SOURCE_RUN_DIR / "ready_for_grid.json").read_text())
if not ready.get("complete") or ready.get("rows") != 294 or ready.get("heldout_accessed") is not False:
    raise ValueError("Producer handoff is incomplete or outside the v2 development scope")
SETTINGS = json.loads((REPO / "grid_analysis.json").read_text())
validate_settings(SETTINGS)
FROZEN_SETTINGS = copy.deepcopy(SETTINGS)
SESSION = (WORK / "grid_analysis_v2/outputs" / SOURCE_RUN_DIR.name /
           datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
SESSION.mkdir(parents=True, exist_ok=False)
write_json(SESSION / "settings_before_review.json", FROZEN_SETTINGS)
(SESSION / "git-revision.txt").write_text(REVISION)
print("Frozen settings and output session:", SESSION)



# %% Cell 5 - Verify the complete producer contract before analysis.
from IPython.display import display

rows, manifest, scope, missing, checks = load_evidence(SOURCE_RUN_DIR, FROZEN_SETTINGS)
if checks["selected_rows"] != 294 or checks["missing_rows"] != 0:
    raise ValueError("Expected the complete 294-row critical-text grid")
if manifest["config"].get("mixing_protocol") != "window_rms_no_wrap_v2":
    raise ValueError("This notebook accepts only the v2 non-looping window calibration")
grid_preview, grid_source = load_performance_grid(
    SOURCE_RUN_DIR, rows, FROZEN_SETTINGS, checks["warnings"]
)
display(grid_preview)
print("Verified rows:", checks["selected_rows"], "Performance grid:", grid_source)
print("DNSMOS is retained as supporting quality evidence; fact recovery defines crossings.")



# %% Cell 6 - Compute paired adjacent-SNR intervals and text-clustered uncertainty.
if SETTINGS != FROZEN_SETTINGS:
    raise ValueError("Settings changed after freezing; start a new session at Cell 4")
OUTPUT = SESSION / "results"
analysis = run_analysis(SOURCE_RUN_DIR, FROZEN_SETTINGS, OUTPUT)
display(analysis["grid"])
display(analysis["intervals"])
print((OUTPUT / "REPORT.md").read_text())



# %% Cell 7 - Display the final CPU-only result and preserve its Drive path.
from IPython.display import Image

for metric in ("wer", "fact_recovery", "estoi"):
    display(Image(filename=str(OUTPUT / f"adjacent_{metric}.png")))
supported = analysis["intervals"][analysis["intervals"].supported_breakpoint]
repeatable = analysis["intervals"][analysis["intervals"].repeatable_deterioration]
display(supported)
display(repeatable)
print("Persistent analysis:", OUTPUT)
print("Share REPORT.md, analysis_record.json and breakpoint_intervals.csv before planning any refinement or intervention.")
