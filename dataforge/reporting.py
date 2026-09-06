"""Baseline diagnostics that remain available even when there is no A/B winner."""

from pathlib import Path

import pandas as pd


def export_baseline(frame, destination):
    """Export only development baseline rows, including missing critical facts."""
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    baseline = frame[(frame.split == "dev") & (frame.variant == "baseline")].copy()
    if baseline.empty:
        raise ValueError("Development baseline results are required")
    summary = baseline.groupby(["condition", "noise_id", "snr_db"], dropna=False).agg(
        clips=("clip_id", "count"), texts=("text_id", "nunique"),
        wer=("wer", "mean"), fact_recovery=("fact_recovery", "mean"),
        estoi=("estoi", "mean"), dnsmos_ovrl=("dnsmos_ovrl", "mean"),
    ).reset_index()
    failures = []
    for row in baseline.to_dict("records"):
        for fact_id, detail in row["fact_details"].items():
            if not detail["recovered"]:
                failures.append({key: row[key] for key in
                                 ("clip_id", "text_id", "replicate", "condition", "reference_text", "transcript", "audio_path")}
                                | {"fact_id": fact_id, "conflict": detail["conflict"]})
    failures = pd.DataFrame(failures, columns=["clip_id", "text_id", "replicate", "condition",
                                             "reference_text", "transcript", "audio_path", "fact_id", "conflict"])
    summary.to_csv(destination / "baseline_condition_summary.csv", index=False)
    failures.to_csv(destination / "baseline_fact_failures.csv", index=False)
    baseline.to_csv(destination / "baseline_results.csv", index=False)
    for metric in ("wer", "fact_recovery", "estoi", "dnsmos_ovrl"):
        fig = Figure(figsize=(8, 4))
        FigureCanvasAgg(fig)
        ax = fig.subplots()
        for noise_id, group in summary[summary.snr_db.notna()].groupby("noise_id"):
            group = group.sort_values("snr_db")
            ax.plot(group.snr_db, group[metric], marker="o", label=noise_id)
        clean = summary.loc[summary.condition == "clean", metric].dropna()
        if not clean.empty:
            ax.axhline(clean.iloc[0], linestyle="--", color="gray", label="clean phone baseline")
        ax.set(xlabel="SNR (dB; lower means more noise)", ylabel=metric,
               title="Development baseline: " + metric)
        if ax.get_legend_handles_labels()[0]:
            ax.legend()
        fig.tight_layout()
        fig.savefig(destination / f"baseline_{metric}.png", dpi=150)
    return summary, failures
