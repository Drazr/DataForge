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
# Imports from a previously used Noise-Masking checkout survive in memory.
loaded_experiment = sys.modules.get("dataforge.experiment")
if loaded_experiment is not None and Path(loaded_experiment.__file__).resolve().parent.parent != REPO.resolve():
    raise RuntimeError("Restart the session, rerun Cells 1-2, then continue at Cell 4 to load the A/B checkout")



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
from dataforge.handoff import copy_run, verify_handoff
SOURCE_NOISE_RUN = WORK / "noise_masking/outputs/6bd1eb398398af0e"
EXPECTED_BASELINE_ID = "6bd1eb398398af0edcbe31d260e15fa71a6e5aca1c3d9abc117aef7028d71966"
# The review ZIP is supporting evidence. The complete run and synthesis cache
# are copied from shared Drive here, including audio absent from that ZIP.
required = ["manifest.json", "baseline_results.csv", "synthesis_cache.json"]
missing = [name for name in required if not (SOURCE_NOISE_RUN / name).is_file()]
if missing or not (SOURCE_NOISE_RUN / "rows").is_dir():
    raise FileNotFoundError(f"Retain the complete baseline folder at {SOURCE_NOISE_RUN}; missing: {missing or ['rows/']}")
import hashlib
source_manifest = json.loads((SOURCE_NOISE_RUN / "manifest.json").read_text())
source_id = hashlib.sha256(json.dumps(source_manifest, sort_keys=True).encode()).hexdigest()
if source_id != EXPECTED_BASELINE_ID:
    raise ValueError("The source does not match the reviewed stress baseline")
COPIED_BASELINE = copy_run(SOURCE_NOISE_RUN, REPO / "inputs/noise_masking", for_delivery=True)
handoff = verify_handoff(COPIED_BASELINE)
print("Copied baseline inputs:", COPIED_BASELINE)
print("Verified handoff files:", len(handoff["files"]))



# %% Cell 5 - Import the frozen baseline; this cell performs no synthesis or ASR.
from google.colab import userdata
from IPython.display import Audio, display
import pandas as pd
from dataforge.delivery import start_delivery
from dataforge.experiment import validate_catalog, validate_challenges, noise_failure_evidence, save_json
RIME_API_KEY = userdata.get("RIME_API_KEY")
experiment = start_delivery(COPIED_BASELINE, WORK / "delivery_ab/outputs")
config, corpus, noises = experiment.config, experiment.corpus, experiment.noises
# Preserve the producer's evaluator configuration; do not silently switch to CPU.
if config["asr_device"] == "cuda":
    import ctranslate2
    if ctranslate2.get_cuda_device_count() < 1:
        raise RuntimeError("This baseline used CUDA/float16. Select a Colab GPU and restart before continuing")
# The original noise datasets and downloaded evaluator models stay in shared Drive.
if not Path(config["asr_local_path"]).is_dir() or not Path(config["dnsmos_model_path"]).is_file():
    raise ValueError("Retain the Noise-Masking evaluator downloads at their original Drive paths")
save_json(experiment.root / "catalog_check.json", validate_catalog(config))
baseline = experiment.all_results("dev")
recurrent = noise_failure_evidence(baseline, config["replicates"])
display(recurrent.groupby("condition").text_id.nunique().rename("recurrent_texts"))
print("Baseline imported without rerunning it; A/B outputs:", experiment.root)



# %% Cell 6 - Freeze one or two challenge conditions from repeatable baseline failures.
# Enter conditions shown in Cell 5 with at least two recurrent texts.
CHALLENGE_CONDITIONS = ["competing_speech_-5dB"]
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
print("Recurrent texts:", sorted(challenge_evidence.text_id.unique()))



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
REVIEW_REPLICATE = 0  # repeat this cell with 1, and each critical text ID
REVIEW_CONDITION = CHALLENGE_CONDITIONS[0]  # also review "clean"
for variant in ("baseline", "clauses", "repeat", "slow"):
    clips = development[(development.text_id == REVIEW_TEXT_ID) & (development.variant == variant)
                        & (development.condition == REVIEW_CONDITION) & (development.replicate == REVIEW_REPLICATE)]
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



# %% Cell 9 - Install the free local audio reviewer (T4 GPU required).
# This adds a post-metrics model-review amendment. It does not access held-out audio.
# Qwen2.5-Omni-7B needs 4-bit loading on a 16 GB T4. If it cannot load, use the
# documented 3B fallback in the next cell; do not silently change the model.
if not __import__("torch").cuda.is_available():
    raise RuntimeError("Select a T4 GPU runtime before running the model review")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--upgrade",
                "git+https://github.com/huggingface/transformers@v4.51.3-Qwen2.5-Omni-preview",
                "accelerate", "bitsandbytes", "qwen-omni-utils"], check=True)
print("Installed the local audio-review dependencies. Continue directly to Cell 10.")



# %% Cell 10 - Run the full development model review without giving the model answer keys.
# T4 preferred: Qwen2.5-Omni-7B in 4-bit mode. Set MODEL_ID to the 3B fallback
# only if Cell 10 reports CUDA out of memory, then restart the runtime and rerun
# Cells 1-2, 4-10. This review is an auxiliary model judgment, not human evidence.
import csv
import hashlib
import re
import time
from datetime import datetime, timezone
import torch
from transformers import BitsAndBytesConfig, Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
from qwen_omni_utils import process_mm_info
from dataforge.experiment import fact_score

MODEL_ID = "Qwen/Qwen2.5-Omni-7B"
MODEL_FALLBACK_ID = "Qwen/Qwen2.5-Omni-3B"
MODEL_REVISION = None  # Pin a Hugging Face commit here only if you need an exact re-run later.
MODEL_REVIEW_ROOT = experiment.root / "model_review_qwen"
MODEL_REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
REVIEW_PROMPT = """Listen to this recording. It may contain competing speakers.
Focus on the appointment, payment, and reference-code message, not unrelated background reading.
Transcribe only words actually audible from the target speaker. Preserve repetitions and contradictions.
Write [unclear] instead of guessing masked words. Do not infer names, numbers, dates, times, or negations.
Assess target speech clarity and audible synthesis artifacts; background speech alone is not an artifact.
Return ONLY valid JSON with these exact fields: transcript (string), clarity (clear|partial|unintelligible),
competing_voice (boolean), artifacts (none|minor|severe|uncertain),
naturalness (acceptable|unacceptable|uncertain), notes (string)."""

queue = development[(development.fact_count > 0) &
                    development.variant.isin(["baseline", "repeat"]) &
                    development.condition.isin(["clean", *CHALLENGE_CONDITIONS])].copy()
queue = queue.sort_values(["text_id", "variant", "replicate", "condition"]).reset_index(drop=True)
expected_rows = len(queue)
if expected_rows == 0:
    raise ValueError("Run Cell 7 before model review")
if set(queue.variant) != {"baseline", "repeat"}:
    raise ValueError("The review queue must contain Baseline and Repeat only")
if queue.audio_path.map(lambda p: Path(p).is_file()).eq(False).any():
    raise FileNotFoundError("The full A/B audio cache is required for review")

quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                  bnb_4bit_use_double_quant=True,
                                  bnb_4bit_compute_dtype=torch.float16)
loaded_config = getattr(globals().get("reviewer"), "config", None)
loaded_model_id = getattr(loaded_config, "_name_or_path", None)
if loaded_model_id == MODEL_ID and "processor" in globals():
    print("Reusing the audio reviewer already loaded in this runtime:", MODEL_ID)
else:
    try:
        reviewer = Qwen2_5OmniForConditionalGeneration.from_pretrained(
            MODEL_ID, revision=MODEL_REVISION, quantization_config=quantization,
            torch_dtype=torch.float16, device_map="auto", low_cpu_mem_usage=True)
    except torch.cuda.OutOfMemoryError as error:
        raise RuntimeError(f"{MODEL_ID} did not fit this GPU. Set MODEL_ID = {MODEL_FALLBACK_ID!r}, restart, and rerun.") from error
    reviewer.disable_talker()  # Text-only review; saves roughly 2 GB of GPU memory.
    reviewer.eval()
    processor = Qwen2_5OmniProcessor.from_pretrained(MODEL_ID, revision=MODEL_REVISION)

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)

def stable_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def parse_review(text):
    text = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", text.strip(), flags=re.I)
    answer = json.loads(text)
    required = {"transcript", "clarity", "competing_voice", "artifacts", "naturalness", "notes"}
    if set(answer) != required or not isinstance(answer["transcript"], str) or not answer["transcript"].strip():
        raise ValueError("Invalid model JSON")
    if answer["clarity"] not in {"clear", "partial", "unintelligible"} or not isinstance(answer["competing_voice"], bool):
        raise ValueError("Invalid clarity/competing_voice")
    if answer["artifacts"] not in {"none", "minor", "severe", "uncertain"} or answer["naturalness"] not in {"acceptable", "unacceptable", "uncertain"}:
        raise ValueError("Invalid quality label")
    return answer

protocol = {
    "review_type": "model", "human_review": "pending", "model_id": MODEL_ID,
    "model_revision": MODEL_REVISION, "quantization": "4-bit NF4 double quantization, float16 compute",
    "prompt": REVIEW_PROMPT, "max_new_tokens": 160, "temperature": 0,
    "scope": "development Baseline/Repeat, clean plus frozen challenge; no held-out audio",
    "amendment": "User requested model review after development metrics and before held-out access.",
}
write_json(MODEL_REVIEW_ROOT / "protocol.json", protocol)
records = []
for index, row in queue.iterrows():
    destination = MODEL_REVIEW_ROOT / "responses" / f"{index:04d}.json"
    audio_path = Path(row.audio_path)
    audio_hash = stable_hash(audio_path)
    if destination.exists():
        record = json.loads(destination.read_text())
        if record.get("audio_sha256") != audio_hash or record.get("model_id") != MODEL_ID:
            raise ValueError("Existing review cache belongs to another input/model; use a new output folder")
    else:
        record = {"text_id": row.text_id, "variant": row.variant, "replicate": int(row.replicate),
                  "condition": row.condition, "audio_path": str(audio_path), "audio_sha256": audio_hash,
                  "model_id": MODEL_ID, "created_utc": datetime.now(timezone.utc).isoformat()}
        conversation = [{"role": "user", "content": [
            {"type": "audio", "audio": str(audio_path)}, {"type": "text", "text": REVIEW_PROMPT}]}]
        started = time.monotonic()
        try:
            prompt = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
            audios, images, videos = process_mm_info(conversation)
            inputs = processor(text=prompt, audio=audios, images=images, videos=videos,
                               return_tensors="pt", padding=True).to("cuda")
            with torch.inference_mode():
                generated = reviewer.generate(**inputs, return_audio=False, do_sample=False, max_new_tokens=160)
            generated = generated[:, inputs.input_ids.shape[1]:]
            raw_text = processor.batch_decode(generated, skip_special_tokens=True,
                                              clean_up_tokenization_spaces=False)[0]
            record["raw_response"] = raw_text
            judgment = parse_review(raw_text)
            facts = next(item["facts"] for item in corpus if item["id"] == row.text_id)
            recovery, details = fact_score(judgment["transcript"], facts)
            record.update(status="ok", judgment=judgment, fact_recovery=recovery, fact_details=details)
        except Exception as error:
            record.update(status="error", error=f"{type(error).__name__}: {error}")
        record["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write_json(destination, record)
    records.append(record)
    print(f"{index + 1}/{expected_rows}: {row.text_id} {row.variant} {row.condition} → {record['status']}")

valid = [record for record in records if record.get("status") == "ok"]
repeat = [record for record in valid if record["variant"] == "repeat"]
complete = len(records) == expected_rows and len(valid) == expected_rows
facts_preserved = complete and bool(repeat) and all(record["fact_recovery"] == 1.0 for record in repeat)
quality_acceptable = complete and bool(repeat) and all(
    record["judgment"]["naturalness"] == "acceptable" and record["judgment"]["artifacts"] in {"none", "minor"}
    for record in repeat)
MODEL_LISTENING_REVIEW = {
    "repeat": {"reviewer_type": "model", "facts_preserved": bool(facts_preserved),
               "quality_acceptable": bool(quality_acceptable), "human_review": "pending",
               "notes": "Qwen2.5-Omni local model review. This is not a human-comprehension claim."}
}
summary = {**protocol, "expected_clips": expected_rows, "successful_clips": len(valid), "complete": complete,
           "model_gate_pass": bool(facts_preserved and quality_acceptable),
           "model_listening_review": MODEL_LISTENING_REVIEW,
           "limitations": ["Model review is not calibrated human listening.",
                           "Errors, missing clips, uncertain naturalness, and incomplete facts fail closed.",
                           "No held-out audio, metric thresholds, or synthesis settings were changed."]}
write_json(MODEL_REVIEW_ROOT / "summary.json", summary)
print(json.dumps(summary, indent=2))



# %% Cell 11 - Freeze the metric-passing candidate using the completed model-review amendment.
# Repeat was the only Cell 7 metric-screen pass. This records the model decision
# separately; it does not represent the review as human evidence.
if not summary["complete"]:
    raise ValueError("Model review is incomplete; resume Cell 10 before selection")
if not summary["model_gate_pass"]:
    raise ValueError("No candidate passes metrics and the conservative model review; report no winner")
selection = experiment.select(CHALLENGE_CONDITIONS, MODEL_LISTENING_REVIEW)
selection["review_protocol"] = "model_review_qwen"
save_json(experiment.root / "selection.json", selection)
print("Frozen candidate:", selection["variant"])



# %% Cell 12 - One held-out validation; resumes use the same cached outputs and candidate.
validation = experiment.run("heldout", ["baseline", selection["variant"]], RIME_API_KEY)
validation_comparison = experiment.comparisons(validation, selection["conditions"])
validation_comparison.to_csv(experiment.root / "heldout_comparison.csv", index=False)
display(validation_comparison)
print("Do not tune the candidate or thresholds on this held-out result. A failure means no validated improvement.")



# %% Cell 13 - Export metrics, plots, and a truthful evidence status.
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
    "development_review": "model; human review pending", "human_heldout_review": "pending", "real_phone_validation": "not run",
    "scope": f"{len(noises)} noise files, fixed text split, simulated 8 kHz PCMU channel; see evidence_scope.json",
    "limitations": "ASR fact recovery is a lexical proxy; no human comprehension study or general noise policy",
})
print("Saved evidence in:", experiment.root)
print("Metric screen passed:", passed, "— verify held-out facts and naturalness before making a final claim.")
validation[validation.fact_count > 0][review_columns].to_csv(
    experiment.root / "heldout_listening_queue.csv", index=False)
