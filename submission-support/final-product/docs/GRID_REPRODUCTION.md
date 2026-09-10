# Reproducing the competing-speech evidence

## Source included in this branch

Grid source was copied from `noise-grid-v2@698fb0e`: `dataforge/`, `fixtures/`,
`tests/`, `experiment.json`, `grid_analysis.json`, the noise-manifest example,
and both requirements files. The Colab entry points use this final branch and
new clone directories; the algorithms and frozen settings are unchanged.
Product source derives from `product-foundation@826a5df`.

## Available and missing artifacts

Available: original pasted Cells 6/7, full supplied analysis CSVs with 294
selected observations and confidence fields, and three selected WAVs.
All three WAV hashes match their observation rows. Full producer audio/cache and
the original producer manifest remain external.

The original result path is recorded in `evidence/noise-grid-v2/provenance.json`.
Transfer that results folder plus the completed producer directory (manifest,
scope, ready marker, score CSVs and referenced audio). Preserve hashes and
code/evaluator versions from `analysis_record.json`; do not infer them from the
current branch. The source baseline/cache and MUSAN recordings are external
dependencies if resynthesizing/rescoring is requested later.

## CPU analysis, no new inference

Use a separate Python 3.12 virtual environment from the product environment:

```powershell
python -m venv .venv-grid
.venv-grid/Scripts/python.exe -m pip install -r requirements-grid.txt
.venv-grid/Scripts/python.exe -m dataforge.grid_analysis --input PATH_TO_COMPLETED_PRODUCER_RUN --config grid_analysis.json --output outputs/grid-reproduction-new
```

The output directory must be new. For Colab, use the seven cells in
`colab_grid_analysis.py`; select the same completed producer run in Cell 1.
Analysis reads saved metrics. Do not rerun producer inference just to regenerate
the report. New analysis timestamps do not alter or replace the original evidence.

`colab_noise_masking.py` is included for procedure reproducibility; its 10 cells
depend on the original verified synthesis cache, model assets and MUSAN data in
Drive. It refuses missing or incompatible inputs. Keep product and evaluator
environments separate to avoid NumPy/SciPy dependency conflicts.

## Audit procedure

Verify source hashes, 294 rows, seven critical texts, two repeats, four noises,
the five frozen SNRs, clean coverage and measured-SNR agreement. Preserve the
0.90 target, four-of-seven recurrence rule and text-level bootstrap settings.
Confirm zero supported breakpoint crossings against the original report.
Inspect matched clean/noisy audio and per-fact records before making a causal or
human-listening claim. Package selected licensed audio with source attribution
and hashes once the producer files are available.
