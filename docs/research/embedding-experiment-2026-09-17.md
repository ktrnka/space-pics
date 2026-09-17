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

## SDO: frame differences find events

Second experiment, same cached week at 6-hour cadence, 512 px thumbnails: per channel, mean absolute difference
between consecutive frames (grayscale, 256 px). Spread is small in absolute terms (rotation dominates a 6-hour
difference) but the outliers agree across channels, which embeddings never did:

| When (UTC) | Channels flagged | Sigma | What it looks like |
|---|---|---|---|
| 09-10 12h to 18h | 94, 335 (the hot flare channels) | +3.9, +4.0 | a bright flare kernel in the active region, visible at 512 px |
| 09-13 06h | 171, 193, 211, composite | +2.3 to +3.2 | large-scale change in the coronal channels, unexamined |

So the ranker for the Sun should be a difference signal at higher cadence (the browse archive has frames every
few minutes), per channel, with the hot channels weighted for flares and the coronagraphs for CMEs. Cheap, no model.

## Perseverance: anomaly finds the unusual, and the unusual is mostly not what we want

815 images (five sols of survey thumbnails plus today's previews), 28 img/s. Rover instruments spread far more
than the Sun: scores from 0.1 to 0.8. Contact sheets (top-8 versus bottom-8 per instrument):

| Instrument | Top outliers | Bottom |
|---|---|---|
| MCZ_RIGHT | ND5 solar-filter sun shots, then four calibration-target frames (grey rings, colour chips, gnomon), one corrupted frame with a dropout band | rock close-ups, repeated |
| MCZ_LEFT | robotic-arm turret hardware shots, sun shots, dark frames | rock close-ups |
| NAVCAM_LEFT | the sun, deck and arm hardware, a self-portrait of the mast shadow | horizons, all alike |
| FRONT_HAZCAM | one sequence (FHAZ02008) dominates the top | the usual view over the wheels |

Keith's reading after looking at the browsable page (more accurate than the sheets): it depends on the instrument.
On some, calibration frames are the most anomalous; on others the least. What the anomaly ordering really exposes is
that each instrument produces several *types* of picture (rocks, hardware checks, calibration, sun, sky, raw Bayer
frames) that the metadata doesn't label. Nothing in the feed says "this is a caltarget frame", and the type mix, not
the centroid, decides where calibration lands. Consequences for the ranker:

- Raw anomaly is a garbage-and-hardware detector first. That's useful (it caught a corrupted frame), but the
  interesting rock or landscape sits in the middle of the distribution, not the tail.
- Filters before ranking: drop ND filters (L7/R7), drop known caltarget sequences (learnable from the anomaly tail),
  drop frames whose mast elevation points at the deck. Then rank what's left, and consider "moderately unusual
  terrain" rather than the extreme tail.
- Or invert the framing: use anomaly to build the exclusion list and let the vision model choose among the rest.
- Better: learn the picture *types* per instrument (cluster the embeddings, label clusters once by eye), then rank
  within a type. The explorer is the labelling tool.

Product codes explain one type. Perseverance image ids carry a product code after the fourth underscore field:
`ECM` is the processed (demosaiced, compressed) image and `EBY` is the raw Bayer-pattern frame, which reads as grey
with a fine checkerboard mask. Mastcam-Z and SuperCam RMI publish both for many exposures (65 EBY vs 117 ECM on
MCZ_LEFT over five sols), so about a third of those candidates are duplicates of another frame in a worse form. The
black-and-white versus colour SuperCam RMI pair is exactly this. Drop `EBY` at extraction.

Other observations from Keith's pass: HMIIC's top anomaly is the day with three large sunspots mid-disc (so for
same-framing sources the tail can still be meaningful); the NAVCAM_LEFT sun frame is a keeper; CHEMCAM_RMI
(Curiosity's telescopic context imager for the laser spectrometer, monochrome, showing the zapped spots) deserves
its own look.

Browsable version: `site/debug/experiment-anomaly.html` (12 most and 6 least anomalous per instrument).

## Curiosity and EPIC

Curiosity's single sequence gives one outlier (a different pointing) and nothing else; too little data. EPIC's Earth
frames barely move (0.02 mean), like the Sun: same-object, same-framing sources need a different signal.
