# Copied upstream evidence

Cell 4 copies the completed Noise-Masking run here, including baseline JSON rows,
clips and cached speech. Optional Grid Analysis conclusions are copied separately.
Inputs remain frozen; new A/B outputs are saved to the delivery folder in Drive.

The supplied review ZIP has been copied locally to
`noise_masking_review/6bd1eb398398af0e/`: 210 score records and 70 verified
critical-text audio clips. Text records and the copy receipt are versioned;
audio remains local because WAVs are excluded by the repository's ignore rules.
The original source ZIP SHA-256 and every copied member hash are in
`review_copy_receipt.json`.

The review archive does not contain all evaluated audio or the source synthesis
cache and request ledger. Cell 4 therefore copies the **complete original Drive
run**, including all 210 clips, JSON rows and synthesis artifacts, into
`inputs/noise_masking/6bd1eb398398af0e/` at runtime. It checks hashes and never
uses the derived `review/` directory as an experiment. Downloads and models stay
at their original shared Drive locations.
