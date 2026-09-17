# Embedding experiment, 2026-09-17

Question: is a per-instrument embedding anomaly score viable as the ranker, and what does the daily job cost?
Setup: DINOv2-small (`facebook/dinov2-small`) via transformers, CPU, pooled output, cosine distance to the
per-instrument centroid. Scratch venv outside the project; script in the session scratchpad (not committed).

## Cost

| Step | Measured |
|---|---|
| Install torch CPU + torchvision + transformers (uv, warm cache) | 24 s; venv is 958 MB |
| Model load (weights cached) | 9 s |
| Embedding throughput, 16-image batches, CPU | 27 images/s |
| 324 images | 12 s |

A daily job embedding a few hundred previews is well under a minute of compute. The cold install in CI is the
unknown; expect one to two minutes, cached thereafter. Fine.

## SDO: global embeddings barely move

Across a week at 6-hour cadence, per-channel anomaly scores span roughly 0.005 to 0.04. Contact sheets of the
top-8 versus bottom-8 per channel look the same to the eye: the disc dominates the embedding, and the things that
make a solar day interesting (a flare, an erupting filament, a CME in a coronagraph) are small or brief. Conclusions:

- A global image embedding is the wrong instrument for the Sun. Better signals: frame-to-frame difference energy
  (a flare or eruption is a large local change), brightness percentiles per channel (flares saturate 94/131/193),
  and for coronagraphs, radial-profile residuals. All cheap and physics-shaped.
- Time-matched comparison across spacecraft (Helioviewer) may be more interesting than anomaly within one.

## Perseverance

(pending: preview images downloading after the date survey finishes)
