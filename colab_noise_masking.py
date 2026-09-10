# %% Cell 1 - Mount Drive; all durable assets and checkpoints live there.
from pathlib import Path
import subprocess
import sys
from google.colab import drive

drive.mount("/content/drive")
REPO = Path("/content/DataForge-noise-grid-v2")
WORK = Path("/content/drive/MyDrive/DataForge")
WORK.mkdir(parents=True, exist_ok=True)
print("Persistent workspace:", WORK)



# %% Cell 2 - Clone the combined v2 generation/analysis branch.
BRANCH = "codex/noise-grid-v2"
REPO_URL = "https://github.com/Drazr/DataForge.git"
if not REPO.exists():
    subprocess.run(["git", "clone", "--single-branch", "--branch", BRANCH, REPO_URL, str(REPO)], check=True)
if (REPO / ".git").exists():
    active = subprocess.check_output(["git", "-C", str(REPO), "branch", "--show-current"], text=True).strip()
    if active != BRANCH:
        raise ValueError(f"Expected {BRANCH}, found {active}; use a separate checkout")
    REVISION = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    print("Branch:", active, "Commit:", REVISION)
    print("Existing checkouts are not updated automatically; use a fresh runtime for newer code.")
else:
    REVISION = "uploaded source archive; retain its source commit separately"
if not (REPO / "dataforge/noise_grid_v2.py").is_file():
    raise ValueError("The v2 branch is incomplete or stale")
sys.path.insert(0, str(REPO))



# %% Cell 3 - Install the pinned evaluator stack. Restart once if Colab requests it.
if sys.version_info[:2] not in {(3, 11), (3, 12), (3, 13)}:
    raise RuntimeError("Use Python 3.11, 3.12 or 3.13")
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
print("Restart the runtime now. Then rerun Cells 1-2 and continue at Cell 4; do not rerun Cell 3.")



# %% Cell 4 - Freeze the critical-text v2 grid and verify the source baseline.
import json
from google.colab import userdata
from dataforge.experiment import Experiment, digest, file_hash, load_corpus, save_json, validate_catalog
from dataforge.downloads import download_musan, prepare_models
from dataforge.noise_grid_v2 import select_noise_panel

SOURCE_BASELINE = WORK / "noise_masking/outputs/6bd1eb398398af0e"
if not SOURCE_BASELINE.is_dir():
    raise ValueError(f"Missing completed stress baseline: {SOURCE_BASELINE}")
source_manifest = json.loads((SOURCE_BASELINE / "manifest.json").read_text())
source_run_id = digest(source_manifest)
if source_run_id != "6bd1eb398398af0edcbe31d260e15fa71a6e5aca1c3d9abc117aef7028d71966":
    raise ValueError("SOURCE_BASELINE manifest does not match the audited producer run")
if source_manifest.get("implementation_sha256") != "50d711004ccafef49d3634550e34e627832a8c44a6d75e9743a9a1b40c89571a":
    raise ValueError("SOURCE_BASELINE uses an unexpected producer implementation")

config = json.loads((REPO / "experiment.json").read_text())
config.update(seed=20260910, snrs_db=[15, 10, 5, 0, -5],
              baseline_profile="noise_grid_v2_critical",
              mixing_protocol="window_rms_no_wrap_v2",
              asr_device="cuda", asr_compute_type="float16")
for key in ("model_id", "speaker", "language", "endpoint", "sample_rate",
            "phone_sample_rate", "speech_rms_dbfs", "asr_repo", "asr_beam_size"):
    if source_manifest["config"][key] != config[key]:
        raise ValueError(f"V2 changed frozen producer control: {key}")
try:
    gpu = subprocess.run(["nvidia-smi", "-L"], check=True, capture_output=True, text=True).stdout.strip()
except (FileNotFoundError, subprocess.CalledProcessError) as error:
    raise RuntimeError("Select a T4 GPU, restart, and rerun Cells 1-2 and 4") from error
print("GPU evaluator:", gpu)

all_corpus = load_corpus(REPO / "fixtures/corpus.json")
corpus = [item for item in all_corpus if item["split"] == "dev" and item["facts"]]
if len(corpus) != 7 or any(item not in source_manifest["corpus"] for item in corpus):
    raise ValueError("Expected the seven unchanged critical development texts")
planned_scores = len(corpus) * config["replicates"] * (1 + 4 * len(config["snrs_db"]))
if planned_scores != 294:
    raise ValueError("Unexpected v2 compute budget")
catalog_check = validate_catalog(config)
try:
    RIME_API_KEY = userdata.get("RIME_API_KEY")
except Exception:
    RIME_API_KEY = None
print("Frozen v2 scores:", planned_scores, "(14 clean + 280 noisy); no held-out texts")
print("Rime key is optional because Cell 7 refuses to run unless all syntheses are cached.")



# %% Cell 5 - Reuse the existing MUSAN copy; no download is expected.
DOWNLOAD_MUSAN = False
if DOWNLOAD_MUSAN:
    musan = download_musan(WORK / "data", Path("/content/musan-download"))
else:
    musan = WORK / "data/musan"
noise_files = sorted(musan.glob("noise/**/*.wav"))
speech_files = sorted(musan.glob("speech/**/*.wav"))
print("Environmental recordings:", len(noise_files), "Speech recordings:", len(speech_files))
if len(noise_files) < 2 or len(speech_files) < 2:
    raise ValueError("A complete MUSAN copy is required; enable DOWNLOAD_MUSAN once if Drive lacks it")



# %% Cell 6 - Deterministically freeze two new speech and two new environmental recordings.
PANEL_SEED = 20260910
MINIMUM_WINDOW_SECONDS = 20.0
pilot_hashes = {noise["sha256"] for noise in source_manifest["noise"]}
noises, panel_audit = select_noise_panel(
    musan, seed=PANEL_SEED, excluded_hashes=pilot_hashes,
    minimum_window_seconds=MINIMUM_WINDOW_SECONDS,
)
panel_path = WORK / "noise_grid_v2/noise_panel.json"
save_json(panel_path, panel_audit)
for noise in noises:
    print(noise["id"], noise["kind"], noise["relative_path"],
          "offset A:", noise["offset_s"], "offset B:", round(noise["offset_b_s"], 3))
print("Frozen panel:", panel_path)
print("Labels come from the MUSAN folder family; verified_by_listening remains false.")



# %% Cell 7 - Resolve models, bind the old synthesis cache, and initialize the resumable run.
config = prepare_models(config, WORK / "models")
source_cache = json.loads((SOURCE_BASELINE / "synthesis_cache.json").read_text())
source_cache_root = Path(source_cache["path"]).parent
experiment = Experiment(config, corpus, noises, WORK / "noise_grid_v2/outputs",
                        synthesis_cache_root=source_cache_root)
missing_cache = []
for item in corpus:
    for replicate in range(config["replicates"]):
        wav, metadata = experiment.synthesis_cache_paths(item, "baseline", replicate)
        if not wav.is_file() or not metadata.is_file():
            missing_cache.append(str(wav))
            continue
        saved = json.loads(metadata.read_text())
        if file_hash(wav) != saved.get("sha256"):
            raise ValueError(f"Cached synthesis hash mismatch: {wav}")
        if saved.get("duration_s", MINIMUM_WINDOW_SECONDS + 1) > MINIMUM_WINDOW_SECONDS:
            raise ValueError("A cached utterance exceeds the frozen non-looping noise window")
if missing_cache:
    raise FileNotFoundError(
        "The 14 required baseline syntheses are not all cached. Restore the audited source cache; "
        "this workflow will not make replacement TTS calls. First missing path: " + missing_cache[0]
    )

save_json(experiment.root / "noise_panel_selection.json", panel_audit)
save_json(experiment.root / "catalog_check.json", catalog_check)
save_json(experiment.root / "evidence_scope.json", {
    "texts_by_split": {"dev": len(corpus), "heldout": 0},
    "critical_texts_by_split": {"dev": len(corpus), "heldout": 0},
    "noise_sources": len(noises), "synthesis_repeats": config["replicates"],
    "snrs_db": config["snrs_db"], "planned_scores": planned_scores,
    "source_baseline_run_id": source_run_id,
    "evidence_level": "exploratory critical-fact ASR proxy; not human comprehension",
})
(experiment.root / "git-revision.txt").write_text(REVISION)
(experiment.root / "pip-freeze.txt").write_text(
    subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
)
(experiment.root / "ffmpeg-version.txt").write_text(
    subprocess.check_output(["ffmpeg", "-version"], text=True)
)
print("Run directory:", experiment.root)
print("Verified all 14 cached baseline syntheses; the remaining work is evaluator-only.")



# %% Cell 8 - Time 12 representative scores; they remain cached for the full run.
import time
from IPython.display import display

sample_texts = [item["id"] for item in corpus[:2]]
started = time.monotonic()
preflight = experiment.run(
    "dev", ["baseline"], RIME_API_KEY,
    item_ids=sample_texts, noise_ids=[noises[0]["id"]], snrs=[15, -5], include_clean=True,
)
elapsed = time.monotonic() - started
if len(preflight) != 12 or not preflight.synthesis_cached.all():
    raise ValueError("Expected 12 evaluator-only preflight scores using cached speech")
noisy_preflight = preflight[preflight.condition != "clean"]
if noisy_preflight.noise_looped.any() or (noisy_preflight.measured_snr_db - noisy_preflight.snr_db).abs().max() > 0.1:
    raise ValueError("Preflight violated the v2 no-loop/measured-SNR contract")
estimate_minutes = elapsed / len(preflight) * planned_scores / 60
save_json(experiment.root / "runtime_preflight.json", {
    "scores": len(preflight), "elapsed_seconds": elapsed,
    "estimated_core_minutes": estimate_minutes, "all_synthesis_cached": True,
    "noise_looped": False, "maximum_snr_error_db": float(
        (noisy_preflight.measured_snr_db - noisy_preflight.snr_db).abs().max()
    ),
})
display(preflight[["text_id", "replicate", "condition", "wer", "fact_recovery", "dnsmos_ovrl"]])
print(f"Timed {len(preflight)} scores in {elapsed / 60:.1f} min; rough full-run estimate: {estimate_minutes:.1f} min.")
print("If quota is insufficient, stop here and resume from the same Drive run in another GPU account.")



# %% Cell 9 - Score the complete 294-row core grid; reruns resume per saved row.
baseline = experiment.run("dev", ["baseline"], RIME_API_KEY)
expected_conditions = 1 + len(noises) * len(config["snrs_db"])
if len(baseline) != len(corpus) * config["replicates"] * expected_conditions:
    raise ValueError("Core grid is incomplete; rerun Cell 9 to resume")
if not baseline.synthesis_cached.all():
    raise ValueError("V2 unexpectedly made a new synthesis request")
noisy = baseline[baseline.condition != "clean"]
if noisy.noise_looped.any() or (noisy.measured_snr_db - noisy.snr_db).abs().max() > 0.1:
    raise ValueError("Completed rows violate v2 mixing controls")
display(baseline.groupby(["noise_id", "snr_db"], dropna=False)[
    ["wer", "fact_recovery", "estoi", "dnsmos_ovrl"]
].mean())



# %% Cell 10 - Export the verified CPU-analysis handoff.
from dataforge.reporting import export_baseline
from dataforge.experiment import noise_failure_evidence

baseline_summary, fact_failures = export_baseline(
    baseline, experiment.root, replicates=config["replicates"]
)
recurrent = noise_failure_evidence(baseline, config["replicates"])
actual_keys = set(baseline[["text_id", "replicate", "condition"]].itertuples(index=False, name=None))
expected_keys = {
    (item["id"], replicate, condition)
    for item in corpus
    for replicate in range(config["replicates"])
    for condition in ["clean"] + [
        f"{noise['id']}_{snr}dB" for noise in noises for snr in config["snrs_db"]
    ]
}
if actual_keys != expected_keys:
    raise ValueError("Handoff refused: the 294-row grid is incomplete or duplicated")
ready = {
    "run_id": experiment.fingerprint, "rows": len(baseline), "complete": True,
    "mixing_protocol": config["mixing_protocol"], "noise_sources": len(noises),
    "snrs_db": config["snrs_db"], "critical_texts": len(corpus),
    "synthesis_repeats": config["replicates"], "heldout_accessed": False,
    "next_step": "Run colab_grid_analysis.py from the same branch in a CPU notebook.",
}
save_json(experiment.root / "ready_for_grid.json", ready)
display(baseline_summary)
display(fact_failures)
display(recurrent)
print(json.dumps(ready, indent=2))
print("Generation complete. Copy the seven cells from colab_grid_analysis.py into a CPU notebook.")
