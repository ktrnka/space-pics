# Experiments

One-off scripts from the 2026-09-17 build day, kept because the techniques are the interesting part and the
results are in `docs/research/embedding-experiment-2026-09-17.md`. They are not part of the pipeline and have their
own dependencies (torch CPU, transformers, numpy, Pillow). Outputs go to `experiments/out/` (gitignored).

Setup, once (about a gigabyte, a minute with a warm cache):

```bash
uv venv --python 3.14 experiments/.venv
uv pip install --python experiments/.venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv pip install --python experiments/.venv/bin/python transformers numpy pillow -e .
mkdir -p experiments/out
```

Then run any script with `experiments/.venv/bin/python experiments/<script>.py` from the repo root, with the image
cache populated (`uv run spacepics download`) or `SPACEPICS_IMAGES_DIR` pointing at one.

## anomaly_embeddings.py

What it teaches: how a self-supervised vision model (DINOv2-small) turns an image into a 384-number vector, and what
"distance from the per-instrument centroid" does and doesn't find. Embeds every cached image, scores each against
its instrument's mean, prints the most and least anomalous per instrument, and writes contact sheets (top 8 versus
bottom 8) so you can see what the tail actually contains. Finding: on rovers the tail is sun shots, calibration
targets, and hardware; on the Sun and Earth the embedding barely moves. Read `E @ cen` and the cosine-distance line
first; that's the whole method.

## sdo_frame_differences.py

What it teaches: for a timelapse, the interesting signal is change since the previous frame, not distance from an
average. Per SDO channel, mean absolute difference between consecutive cached frames, then which frames stand out in
standard deviations, with a contact sheet. Finding: a flare on 09-10 lights up 94 and 335 Å at four sigma, and the
coronal channels agree on a second event on 09-13, where embeddings saw nothing. About 40 lines; the numpy is the
lesson.

## wigglegram_poc.py

What it teaches: aligning a stereo pair by normalised cross-correlation over a search window, why aligning on the
subject (centre band) beats aligning on the whole frame, and how to measure depth as the difference between the
best shift for the far band and the near band ("parallax spread"). The production version is
`src/spacepics/wiggle.py`; this one also writes side-by-side check sheets per pair and shows the pair-selection rule
(8 to 40 px of spread) being derived.
