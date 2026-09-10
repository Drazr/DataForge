"""Offline adjacent-SNR analysis of Noise Masking or Noise-Conditioned A/B exports.

No metric inference, intervention selection, or external services are invoked.
All positive differences mean deterioration. Repeats are clustered by text.
The completed baseline export is sufficient; an A/B winner is not required.
"""

import argparse
import hashlib
import itertools
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


METRICS = ("wer", "fact_recovery", "estoi")
GRID_METRICS = (*METRICS, "dnsmos_ovrl")
KEYS = ["text_id", "replicate", "condition"]
REQUIRED = [
    "run_id", "split", "variant", "clip_id", *KEYS, "noise_id", "snr_db",
    "measured_snr_db", "noise_file", "noise_sha256", "noise_offset_s",
    "noise_kind", "noise_reference_rms", "sample_rate", "speech_level_method",
    "model_id", "speaker", "endpoint", "transport", "noise_placement",
        "source_audio", "duration_s", "fact_count", "audio_path", *GRID_METRICS,
]
INTERVAL_COLUMNS = [
    "noise_id", "noise_kind", "higher_snr_db", "lower_snr_db",
    "higher_condition", "lower_condition", "metric", "expected_pairs",
    "matched_pairs", "complete_grid_pair", "eligible_texts", "complete_texts",
    "mean_higher", "mean_lower", "mean_deterioration", "text_delta_sd",
    "ci95_low", "ci95_high", "consistent_texts", "consistent_fraction",
    "repeatable_deterioration", "acceptance_limit", "acceptance_status",
    "crossing_texts", "crossing_fraction", "supported_breakpoint",
    "measured_snr_higher_mean", "measured_snr_lower_mean",
    "measured_snr_non_decreasing_pairs",
]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_settings(settings):
    if settings["input_file"] not in {"baseline_results.csv", "results.csv"}:
        raise ValueError("Choose exactly one of baseline_results.csv or results.csv")
    if settings["split"] not in {"dev", "heldout"}:
        raise ValueError("split must be dev or heldout")
    if settings["input_file"] == "baseline_results.csv" and (
        settings["split"] != "dev" or settings["variant"] != "baseline"
    ):
        raise ValueError("baseline_results.csv contains development baseline only; use results.csv otherwise")
    a = settings["acceptance"]
    for key in ("maximum_wer", "minimum_fact_recovery"):
        value = a[key]
        if value is not None and (not isinstance(value, (int, float)) or
                                  not np.isfinite(value) or value < 0):
            raise ValueError(f"Invalid {key}")
    if a["minimum_fact_recovery"] is not None and a["minimum_fact_recovery"] > 1:
        raise ValueError("Fact recovery limits use a fraction from 0 to 1")
    if any(a[k] is not None for k in ("maximum_wer", "minimum_fact_recovery")):
        if not a["rationale"].strip() or a["established_before_review"] is not True:
            raise ValueError("Record the acceptance rationale and confirm limits were established before review")
    r = settings["repeatability"]
    for key in ("minimum_texts", "minimum_repeats"):
        if type(r[key]) is not int or r[key] < 2:
            raise ValueError(f"{key} must be an integer >= 2")
    if not 0 < r["minimum_text_fraction"] <= 1:
        raise ValueError("minimum_text_fraction must be in (0, 1]")
    for metric in METRICS:
        value = r["minimum_deterioration"][metric]
        if not isinstance(value, (int, float)) or not np.isfinite(value) or value < 0:
            raise ValueError("Minimum deterioration must be finite and nonnegative")
    if type(settings["bootstrap_samples"]) is not int or not 100 <= settings["bootstrap_samples"] <= 100000:
        raise ValueError("bootstrap_samples must be an integer between 100 and 100000")


def load_evidence(directory, settings):
    """Validate the producer's contract and report missing expected observations."""
    validate_settings(settings)
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    config = manifest["config"]
    scope_path = directory / "evidence_scope.json"
    if scope_path.is_file():
        scope = read_json(scope_path)
        scope_source = "evidence_scope.json"
    else:
        # All planned counts already exist in the producer's hashed manifest.
        splits = {item["split"] for item in manifest["corpus"]}
        scope = {
            "synthesis_repeats": config["replicates"], "snrs_db": config["snrs_db"],
            "noise_sources": len(manifest["noise"]),
            "texts_by_split": {s: sum(x["split"] == s for x in manifest["corpus"]) for s in splits},
            "critical_texts_by_split": {
                s: sum(x["split"] == s and bool(x["facts"]) for x in manifest["corpus"]) for s in splits
            },
        }
        scope_source = "derived from manifest.json"
    run_id = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    if not (directory / settings["input_file"]).is_file():
        raise FileNotFoundError(
            f"Missing {settings['input_file']}. Run colab_noise_masking.py through Cell 10 "
            "to complete and export the v2 producer grid."
        )
    raw = pd.read_csv(directory / settings["input_file"])
    missing_columns = sorted(set(REQUIRED) - set(raw.columns))
    if missing_columns:
        raise ValueError(f"Missing required producer fields: {missing_columns}")
    if set(raw.run_id.dropna()) != {run_id} or raw.run_id.isna().any():
        raise ValueError("CSV run_id does not match manifest.json; use files from one original run")
    frame = raw[(raw.split == settings["split"]) & (raw.variant == settings["variant"])].copy()
    if frame.empty:
        raise ValueError("No rows match the requested split and variant")
    if frame.duplicated(KEYS).any() or frame.clip_id.duplicated().any():
        raise ValueError("Duplicate observations; do not concatenate overlapping baseline exports")
    if frame[["clip_id", *KEYS, "noise_id", "audio_path"]].isna().any().any():
        raise ValueError("Missing observation identifiers or audio paths")
    for column in ["replicate", "snr_db", "measured_snr_db", "fact_count", *GRID_METRICS]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if np.isinf(frame[column]).any():
            raise ValueError(f"Infinite value in {column}")
    if frame.wer.isna().any() or (frame.wer < 0).any():
        raise ValueError("WER must be nonnegative and present (values above 1 are valid)")
    if frame.dnsmos_ovrl.isna().any() or not np.isfinite(frame.dnsmos_ovrl).all():
        raise ValueError("DNSMOS OVRL must be finite and present as supporting evidence")
    facts = frame.fact_count > 0
    if frame.loc[facts, "fact_recovery"].isna().any() or not frame.loc[facts, "fact_recovery"].between(0, 1).all():
        raise ValueError("Critical clips require fact_recovery between 0 and 1")
    if frame.loc[~facts, "fact_recovery"].notna().any():
        raise ValueError("General clips must retain blank fact_recovery")
    noisy = frame.condition != "clean"
    if frame.loc[noisy, ["snr_db", "measured_snr_db", "estoi"]].isna().any().any():
        raise ValueError("Noisy clips require nominal/measured SNR and ESTOI")
    if not frame.loc[noisy, "estoi"].between(-1, 1).all():
        raise ValueError("ESTOI outside its correlation range")
    if frame.loc[~noisy, ["snr_db", "estoi"]].notna().any().any():
        raise ValueError("Clean reference must have blank SNR and ESTOI")
    for field, expected in {
        "model_id": config["model_id"], "speaker": config["speaker"],
        "endpoint": config["endpoint"], "sample_rate": config["phone_sample_rate"],
        "speech_level_method": manifest["speech_level_method"],
        "transport": "HTTP WAV -> local PCMU roundtrip",
        "noise_placement": "after simulated phone codec",
    }.items():
        if not frame[field].eq(expected).all():
            raise ValueError(f"Inconsistent control: {field}")
    corpus = [x for x in manifest["corpus"] if x["split"] == settings["split"]]
    expected_texts = {x["id"]: len(x["facts"]) for x in corpus}
    if not expected_texts or len(expected_texts) != len(corpus):
        raise ValueError("Missing or duplicate corpus IDs")
    if not frame.fact_count.eq(frame.text_id.map(expected_texts)).all():
        raise ValueError("Text IDs or fact counts disagree with the manifest corpus")
    snrs = config["snrs_db"]
    repeats = config["replicates"]
    if type(repeats) is not int or repeats < 1 or len(set(snrs)) != len(snrs) or len(snrs) < 2 or not np.isfinite(snrs).all():
        raise ValueError("Manifest needs valid repeats and at least two distinct finite SNRs")
    if (scope["synthesis_repeats"] != repeats or scope["snrs_db"] != snrs or
        scope["noise_sources"] != len(manifest["noise"]) or
        scope["texts_by_split"][settings["split"]] != len(corpus) or
        scope["critical_texts_by_split"][settings["split"]] != sum(v > 0 for v in expected_texts.values())):
        raise ValueError("evidence_scope.json disagrees with manifest.json")
    conditions = {"clean": ("clean", None)}
    for noise in manifest["noise"]:
        rows = frame[frame.noise_id == noise["id"]]
        for field, expected in {"noise_file": noise["path"], "noise_sha256": noise["sha256"],
                                "noise_offset_s": noise["offset_s"],
                                "noise_reference_rms": noise["reference_rms"],
                                "noise_kind": noise.get("kind", noise["id"])}.items():
            ok = np.isclose(rows[field], expected) if isinstance(expected, (int, float)) else rows[field].eq(expected)
            if not np.all(ok):
                raise ValueError(f"Noise control mismatch: {noise['id']} / {field}")
        for snr in snrs:
            conditions[f"{noise['id']}_{snr}dB"] = (noise["id"], snr)
    for row in frame.itertuples():
        if row.condition not in conditions:
            raise ValueError(f"Unexpected condition: {row.condition}")
        noise_id, snr = conditions[row.condition]
        if row.noise_id != noise_id or (snr is not None and row.snr_db != snr):
            raise ValueError("Condition label disagrees with noise/SNR metadata")
    if config.get("mixing_protocol") == "window_rms_no_wrap_v2":
        v2_required = {"mixing_protocol", "noise_window_rms", "noise_gain", "noise_looped",
                       "source_audio_sha256"}
        absent = sorted(v2_required - set(frame.columns))
        if absent:
            raise ValueError(f"V2 rows are missing mixing fields: {absent}")
        if not frame.mixing_protocol.eq("window_rms_no_wrap_v2").all():
            raise ValueError("V2 mixing protocol changed within the run")
        if not frame.source_audio_sha256.astype(str).str.fullmatch(r"[0-9a-f]{64}").all():
            raise ValueError("Invalid v2 source-audio hash")
        for column in ("noise_window_rms", "noise_gain"):
            values = pd.to_numeric(frame.loc[noisy, column], errors="raise")
            if values.isna().any() or not np.isfinite(values).all() or (values <= 0).any():
                raise ValueError(f"Invalid v2 {column}")
        looped = frame.loc[noisy, "noise_looped"]
        if looped.dtype != bool:
            normalized = looped.astype(str).str.lower().map({"true": True, "false": False})
            if normalized.isna().any():
                raise ValueError("Invalid v2 noise_looped value")
            looped = normalized
        if looped.any():
            raise ValueError("V2 noise windows must never loop")
        if (frame.loc[noisy, "measured_snr_db"] - frame.loc[noisy, "snr_db"]).abs().max() > 0.1:
            raise ValueError("V2 measured SNR differs from its request by more than 0.1 dB")
    # One speech realization must be reused across SNRs, including its clean reference.
    control_columns = ["source_audio", "duration_s"]
    if config.get("mixing_protocol") == "window_rms_no_wrap_v2":
        control_columns.append("source_audio_sha256")
    controls = frame.groupby(["text_id", "replicate"])[control_columns].nunique(dropna=False)
    if (controls != 1).any().any():
        raise ValueError("Speech source/duration changes across matched conditions")
    if config.get("mixing_protocol") == "window_rms_no_wrap_v2":
        windows = frame[noisy].groupby(["text_id", "replicate", "noise_id"])["noise_window_rms"].nunique()
        if (windows != 1).any():
            raise ValueError("V2 noise window changed across SNRs")
    expected_keys = set(itertools.product(expected_texts, range(repeats), conditions))
    actual_keys = set(frame[KEYS].itertuples(index=False, name=None))
    if actual_keys - expected_keys:
        raise ValueError("Unexpected text/repeat/condition observations")
    missing = pd.DataFrame(sorted(expected_keys - actual_keys), columns=KEYS)
    report = {
        "run_id": run_id, "input_file": settings["input_file"], "split": settings["split"],
        "variant": settings["variant"], "expected_rows": len(expected_keys),
        "selected_rows": len(frame), "missing_rows": len(missing),
        "scope_source": scope_source,
        "warnings": ["Incomplete intervals cannot support breakpoint claims"] if len(missing) else [],
    }
    return frame, manifest, scope, missing, report


def summarize_grid(frame):
    """Equal text weighting; fact means exclude texts without labeled facts."""
    records = []
    for condition, rows in frame.groupby("condition", sort=False):
        record = {"condition": condition, "noise_id": rows.noise_id.iloc[0],
                  "snr_db": rows.snr_db.iloc[0], "clips": len(rows), "texts": rows.text_id.nunique(),
                  "critical_clips": int(rows.fact_recovery.notna().sum())}
        for metric in GRID_METRICS:
            record[metric] = rows.groupby("text_id")[metric].mean().mean()
        for stat in ("mean", "min", "max"):
            record[f"measured_snr_db_{stat}"] = getattr(rows.measured_snr_db, stat)()
        records.append(record)
    return pd.DataFrame(records)


def load_performance_grid(directory, frame, settings, warnings):
    """Reuse matching producer means/counts; derive only absent or inapplicable grids.

The inexpensive aggregation below checks freshness and adds measured-SNR ranges.
It does not regenerate speech, metric scores, or existing baseline plots.
"""
    derived = summarize_grid(frame)
    path = Path(directory) / "baseline_condition_summary.csv"
    if settings["split"] != "dev" or settings["variant"] != "baseline" or not path.is_file():
        return derived, "derived from selected observations"
    columns = ["condition", "noise_id", "snr_db", "clips", "texts", "critical_clips", *GRID_METRICS]
    try:
        saved = pd.read_csv(path)
        if not set(columns).issubset(saved) or saved.condition.duplicated().any():
            raise ValueError("incompatible columns or duplicate conditions")
        saved = saved[columns].set_index("condition").sort_index()
        expected = derived.set_index("condition").sort_index()
        if not saved.index.equals(expected.index) or not saved.noise_id.equals(expected.noise_id):
            raise ValueError("condition/noise coverage differs")
        for column in ["snr_db", "clips", "texts", "critical_clips", *GRID_METRICS]:
            if not np.allclose(saved[column], expected[column], rtol=1e-9, atol=1e-12, equal_nan=True):
                raise ValueError(f"{column} differs from selected observations")
        # Preserve producer metric values, adding only the measured-SNR diagnostics.
        measured = [c for c in expected if c.startswith("measured_snr_db_")]
        return saved.join(expected[measured]).reset_index(), path.name
    except (ValueError, TypeError, pd.errors.ParserError) as error:
        warnings.append(f"Baseline summary not reused ({error}); derived grid from selected observations")
        return derived, "derived from selected observations"


def interval_analysis(frame, manifest, settings):
    """Pair only adjacent *planned* levels, never bridge a missing intermediate SNR."""
    intervals, all_pairs = [], []
    repeats = manifest["config"]["replicates"]
    snrs = sorted(manifest["config"]["snrs_db"], reverse=True)
    corpus = [x for x in manifest["corpus"] if x["split"] == settings["split"]]
    rules = settings["repeatability"]
    rng = np.random.default_rng(settings["seed"])
    for noise in manifest["noise"]:
        for high, low in zip(snrs, snrs[1:]):
            hi_condition, lo_condition = f"{noise['id']}_{high}dB", f"{noise['id']}_{low}dB"
            hi = frame[frame.condition == hi_condition]
            lo = frame[frame.condition == lo_condition]
            pairs = hi.merge(lo, on=["text_id", "replicate"], suffixes=("_higher", "_lower"), validate="one_to_one")
            pairs["higher_snr_db"], pairs["lower_snr_db"] = high, low
            pairs["noise_id"] = noise["id"]
            for metric in METRICS:
                sign = 1 if metric == "wer" else -1
                pairs[f"{metric}_deterioration"] = sign * (pairs[f"{metric}_lower"] - pairs[f"{metric}_higher"])
            all_pairs.append(pairs)
            complete = len(pairs) == len(corpus) * repeats
            for metric in METRICS:
                eligible = sum(bool(x["facts"]) for x in corpus) if metric == "fact_recovery" else len(corpus)
                valid = pairs.dropna(subset=[f"{metric}_higher", f"{metric}_lower"]).copy()
                counts = valid.groupby("text_id").replicate.nunique()
                valid = valid[valid.text_id.isin(counts[counts == repeats].index)]
                grouped = valid.groupby("text_id")
                deltas = grouped[f"{metric}_deterioration"].mean()
                n = len(deltas)
                threshold = rules["minimum_deterioration"][metric]
                minima = grouped[f"{metric}_deterioration"].min()
                consistent = int(((minima >= threshold) if threshold > 0 else (minima > 0)).sum())
                enough = complete and repeats >= rules["minimum_repeats"] and n == eligible and n >= rules["minimum_texts"]
                mean_delta = float(deltas.mean())
                repeatable = (enough and consistent >= rules["minimum_texts"] and
                              consistent / max(eligible, 1) >= rules["minimum_text_fraction"] and
                              (mean_delta >= threshold if threshold > 0 else mean_delta > 0))
                ci = [float("nan"), float("nan")]
                if n >= 2:
                    # Resample texts, retaining all their repeats together (no pseudo-replication).
                    draws = rng.choice(deltas.to_numpy(), size=(settings["bootstrap_samples"], n), replace=True)
                    ci = np.quantile(draws.mean(axis=1), [0.025, 0.975])
                means = [grouped[f"{metric}_{side}"].mean().mean() for side in ("higher", "lower")]
                limit = settings["acceptance"].get("maximum_wer" if metric == "wer" else "minimum_fact_recovery") if metric != "estoi" else None
                crossing, status, supported = 0, "supporting_metric" if metric == "estoi" else "limits_not_set", False
                if limit is not None and n:
                    high_ok = valid[f"{metric}_higher"] <= limit if metric == "wer" else valid[f"{metric}_higher"] >= limit
                    low_ok = valid[f"{metric}_lower"] <= limit if metric == "wer" else valid[f"{metric}_lower"] >= limit
                    valid["crosses"] = high_ok & ~low_ok
                    crossing = int(valid.groupby("text_id").crosses.all().sum())
                    hi_ok = means[0] <= limit if metric == "wer" else means[0] >= limit
                    lo_ok = means[1] <= limit if metric == "wer" else means[1] >= limit
                    status = ("crosses_limit" if hi_ok and not lo_ok else "both_acceptable" if hi_ok and lo_ok
                              else "already_unacceptable_at_higher_snr" if not hi_ok and not lo_ok
                              else "nonmonotonic_recovery")
                    supported = (enough and status == "crosses_limit" and crossing >= rules["minimum_texts"] and
                                 crossing / max(eligible, 1) >= rules["minimum_text_fraction"])
                elif limit is not None:
                    status = "no_complete_texts"
                intervals.append(dict(
                    noise_id=noise["id"], noise_kind=noise.get("kind", noise["id"]),
                    higher_snr_db=high, lower_snr_db=low, higher_condition=hi_condition, lower_condition=lo_condition,
                    metric=metric, expected_pairs=len(corpus) * repeats, matched_pairs=len(pairs),
                    complete_grid_pair=complete, eligible_texts=eligible, complete_texts=n,
                    mean_higher=means[0], mean_lower=means[1], mean_deterioration=mean_delta,
                    text_delta_sd=deltas.std(ddof=1), ci95_low=ci[0], ci95_high=ci[1],
                    consistent_texts=consistent, consistent_fraction=consistent / eligible if eligible else np.nan,
                    repeatable_deterioration=repeatable, acceptance_limit=limit, acceptance_status=status,
                    crossing_texts=crossing, crossing_fraction=crossing / eligible if eligible else np.nan,
                    supported_breakpoint=supported,
                    measured_snr_higher_mean=pairs.measured_snr_db_higher.mean(),
                    measured_snr_lower_mean=pairs.measured_snr_db_lower.mean(),
                    measured_snr_non_decreasing_pairs=int((pairs.measured_snr_db_lower >= pairs.measured_snr_db_higher).sum()),
                ))
    return pd.DataFrame(intervals, columns=INTERVAL_COLUMNS), pd.concat(all_pairs, ignore_index=True)


def remap_audio(value, mapping):
    normalized = str(value).replace("\\", "/")
    for old, new in sorted(mapping.items(), key=lambda item: -len(item[0])):
        prefix = old.replace("\\", "/").rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return new.replace("\\", "/").rstrip("/") + normalized[len(prefix):]
    return normalized


def challenge_cases(directory, frame, intervals, settings, warnings):
    """Link producer evidence; never freeze a challenge or select an A/B winner."""
    evidence_columns = ["text_id", "replicate", "condition", "fact_id", "clean_clip_id",
                        "noisy_clip_id", "clean_audio_path", "audio_path"]
    output_columns = [*evidence_columns, "reference_text", "transcript", "conflict", "basis",
                      "resolved_audio_path", "resolved_clean_audio_path", "audio_available", "clean_audio_available"]
    if settings["split"] != "dev" or settings["variant"] != "baseline":
        warnings.append("Challenge export disabled: only development baseline may select challenge cases")
        return pd.DataFrame(columns=output_columns)
    evidence_path = Path(directory) / "noise_failure_evidence.csv"
    failures_path = Path(directory) / "baseline_fact_failures.csv"
    if not evidence_path.exists() or not failures_path.exists():
        warnings.append("Missing fact-detail/evidence CSV: intervals are available, challenge links are not")
        return pd.DataFrame(columns=output_columns)
    evidence = pd.read_csv(evidence_path)
    failures = pd.read_csv(failures_path)
    if not set(evidence_columns).issubset(evidence.columns):
        raise ValueError("noise_failure_evidence.csv has an incompatible schema")
    required_failures = ["clip_id", "fact_id", "reference_text", "transcript", "conflict"]
    if not set(required_failures).issubset(failures.columns):
        raise ValueError("baseline_fact_failures.csv has an incompatible schema")
    if evidence.duplicated([*KEYS, "fact_id"]).any() or failures.duplicated(["clip_id", "fact_id"]).any():
        raise ValueError("Duplicate fact evidence")
    # Verify links belong to this selected run before using a producer's diagnostic export.
    selected = frame.set_index("clip_id")
    for row in evidence.itertuples():
        for clip, condition, path in [(row.noisy_clip_id, row.condition, row.audio_path),
                                       (row.clean_clip_id, "clean", row.clean_audio_path)]:
            if clip not in selected.index:
                raise ValueError("Fact evidence references clips outside the selected input")
            actual = selected.loc[clip]
            if (actual.text_id, actual.replicate, actual.condition, actual.audio_path) != (row.text_id, row.replicate, condition, path):
                raise ValueError("Fact evidence metadata does not match selected observations")
    primary = intervals[intervals.metric.isin(["wer", "fact_recovery"])]
    chosen = primary[primary.repeatable_deterioration | primary.supported_breakpoint]
    evidence = evidence[evidence.condition.isin(chosen.lower_condition)].copy()
    if evidence.empty:
        return pd.DataFrame(columns=output_columns)
    enriched = evidence.merge(failures[required_failures], left_on=["noisy_clip_id", "fact_id"],
                              right_on=["clip_id", "fact_id"], how="left", validate="one_to_one", indicator=True)
    if not enriched._merge.eq("both").all():
        raise ValueError("Noise evidence has no matching baseline fact failure")
    enriched["basis"] = enriched.condition.map({
        condition: "; ".join(f"{r.metric}: {'limit crossing' if r.supported_breakpoint else 'repeatable deterioration'} "
                             f"({r.higher_snr_db} to {r.lower_snr_db} dB)" for r in group.itertuples())
        for condition, group in chosen.groupby("lower_condition")
    })
    for column, resolved, available in [("audio_path", "resolved_audio_path", "audio_available"),
                                         ("clean_audio_path", "resolved_clean_audio_path", "clean_audio_available")]:
        enriched[resolved] = enriched[column].map(lambda x: remap_audio(x, settings["audio_path_remap"]))
        enriched[available] = enriched[resolved].map(lambda x: Path(x).is_file())
    if not (enriched.audio_available & enriched.clean_audio_available).all():
        warnings.append("Some linked audio is unavailable; copy the clips or configure audio_path_remap")
    return enriched[output_columns]


def save_plots(intervals, output):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    for metric in METRICS:
        rows = intervals[intervals.metric == metric].reset_index(drop=True)
        fig = Figure(figsize=(10, 4))
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        x = np.arange(len(rows))
        ax.scatter(x, rows.mean_deterioration)
        ax.vlines(x, rows.ci95_low, rows.ci95_high, color="gray")
        ax.axhline(0, color="black", linewidth=0.7)
        ax.set_xticks(x, [f"{r.noise_id}\n{r.higher_snr_db:g} to {r.lower_snr_db:g} dB" for r in rows.itertuples()], rotation=25)
        ax.set(ylabel="Deterioration (positive = worse)",
               title=f"{metric}: paired text means, exploratory 95% text-bootstrap intervals")
        fig.tight_layout()
        fig.savefig(Path(output) / f"adjacent_{metric}.png", dpi=150)


def run_analysis(directory, settings, output):
    """Write a fresh analysis folder, preserving producer outputs and earlier analyses."""
    directory, output = Path(directory).resolve(), Path(output).resolve()
    if output == directory or output in directory.parents:
        raise ValueError("Output must be a new analysis folder, not the evidence folder or its parent")
    frame, manifest, scope, missing, report = load_evidence(directory, settings)
    intervals, pairs = interval_analysis(frame, manifest, settings)
    grid, grid_source = load_performance_grid(directory, frame, settings, report["warnings"])
    cases = challenge_cases(directory, frame, intervals, settings, report["warnings"])
    output.mkdir(parents=True, exist_ok=False)
    for name, data in {"selected_observations": frame, "analysis_grid": grid,
                       "missing_observations": missing, "adjacent_pairs": pairs,
                       "breakpoint_intervals": intervals, "development_challenge_cases": cases}.items():
        data.to_csv(output / f"{name}.csv", index=False)
    save_plots(intervals, output)
    report.update({
        "created_utc": datetime.now(timezone.utc).isoformat(), "settings": settings,
        "grid_source": grid_source,
        "source_hashes": {p.name: sha256(p) for p in [directory / settings["input_file"],
                          directory / "manifest.json", directory / "evidence_scope.json",
                          directory / "baseline_fact_failures.csv", directory / "noise_failure_evidence.csv",
                          directory / "baseline_condition_summary.csv"] if p.is_file()},
        "analysis_code_sha256": sha256(__file__), "evidence_scope": scope,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "supported_metric_intervals": int(intervals.supported_breakpoint.sum()),
        "challenge_rows": len(cases),
        "limitations": ["Pilot evidence; no universal threshold or classifier",
                        "WER and fact recovery are ASR proxies, not measured human comprehension",
                        "SNR intervals use nominal calibration; inspect measured SNR differences",
                        "Bootstrap resamples texts, not repeats; small-sample intervals are exploratory",
                        "No multiplicity correction; recurrence settings are pilot choices, not statistical guarantees",
                        "DNSMOS is supporting quality evidence and does not define a breakpoint"],
    })
    write_json(output / "analysis_record.json", report)
    a = settings["acceptance"]
    status = "Deterioration only: no acceptance limits supplied." if a["maximum_wer"] is None and a["minimum_fact_recovery"] is None else "Only metrics with configured acceptance limits can identify unacceptable performance."
    lines = ["# Grid and breakpoint analysis", "", status, "",
             f"Selected {len(frame)} rows; {len(missing)} expected rows missing.",
             f"Performance grid: {grid_source}. Scope: {report['scope_source']}.",
             f"Supported metric/interval crossings: {report['supported_metric_intervals']}.",
             f"Development challenge rows: {len(cases)}.", "",
             "See breakpoint_intervals.csv for matched counts, nominal/measured SNR, recurrence, and uncertainty.",
             "No supported interval means the present grid supplies insufficient crossing evidence; it does not prove all conditions acceptable.",
             "Challenge rows are candidates for the separate A/B workflow; no challenge.json was written.", "",
             *["- " + x for x in report["warnings"] + report["limitations"]], ""]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return {"grid": grid, "intervals": intervals, "pairs": pairs, "challenges": cases, "report": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Noise Masking or Noise-Conditioned A/B run directory (baseline sufficient)")
    parser.add_argument("--config", type=Path, default=Path("grid_analysis.json"))
    parser.add_argument("--output", required=True, type=Path, help="New folder; existing folders are refused")
    args = parser.parse_args()
    result = run_analysis(args.input, read_json(args.config), args.output)
    print(f"Saved {len(result['intervals'])} metric intervals to {args.output}")


if __name__ == "__main__":
    main()
