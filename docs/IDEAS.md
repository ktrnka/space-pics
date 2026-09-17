# Ideas

A parking lot for things noticed while looking at the output. Not commitments. When one is ready to be worked on, it
moves to `docs/TASKS.md` with a file set and comes off this list. Settled questions go under Findings so nobody
re-asks them.

Format: one bullet per idea, dated, with where it came from and enough context to evaluate it cold.

## Image processing

- **Colour-correct Mastcam-Z frames against the calibration target** (2026-09-17, perseverance explorer). The raw-feed
  browse JPEGs are uncalibrated; the team's "natural colour" and "white-balanced" releases use the deck calibration
  target (grey rings, colour chips, shadow post). Could we find caltarget frames (fixed mast pointing), estimate
  per-channel gains from the chips' known reflectances, and apply them to same-sol frames? Limits: 8-bit JPEGs with
  unknown onboard processing, so "looks right", not science-grade. Depends on picture-type labels to find the frames.
- **Mastcam-Z near-IR decorrelation stretch** (2026-09-17, Keith). The right eye's 800-1022 nm filters target
  iron-mineral absorption features; the team publishes band-ratio and decorrelation-stretch composites that make rock
  composition visible. Same sequence, same eye, no alignment needed. Day-sized, and the chooser seam already supports
  derived images.
- **Use press-release images as targets for composite tuning** (2026-09-17, Keith). Match an ESA/NASA finished image to
  the raw frames it came from, then tune our composite pipeline against it. For Webb that means raw per-filter frames
  via MAST (FITS-sized). Less guess-and-check.
- **Feature the ND solar-filter frames as an occasional treat** (2026-09-17). L7/R7 frames are Sun shots for dust
  opacity and Phobos/Deimos transits; they're excluded from picking now, but a transit is worth showing.
- **Build our own SUVI composite** (2026-09-17, Keith). SUVI has the same channel set as AIA; a 3-channel composite
  beside AIA's 211/193/171 makes a two-spacecraft comparison. Other AIA composites worth trying: 304/171/193, and
  094/335/193 for flares.
- **Sun story arcs** (2026-09-17). An eruption on the disc (AIA 304/171) becomes a CME in LASCO hours later; the
  difference detector could pair them automatically. Keith: "I'm not sure what story would be interesting from the
  Sun views, I have more questions than anything", so this needs a worked example before it's a task.

## Learning layer

- **Mission-select screen** (2026-09-17, Keith). A UI showing where each spacecraft is relative to Earth and the Sun,
  like a game's mission select. The vehicle sketch on the board is the first step.
- **Classic space UI theme, or a Mass Effect one** (2026-09-17, Keith). Pure fun; the site is deliberately bare today.
- **Curiosity A-side / B-side, and left / right, discoverable from a post** (2026-09-17, Keith). The explorer link per
  panel gets you to the sequence; a "see the other eye" link would be the direct version.

## Image selection

- **Navcam love** (2026-09-17, Keith). Navcam frames deserve a fair share; don't let ranking bury them.
- **Keepers noticed by eye** (2026-09-17): the NAVCAM_LEFT sun frame; the HMIIC day with three big sunspots; GOES
  GeoColor composites, far better than expected; CHEMCAM_RMI deserves a dedicated look.
- **Digest recipes beyond seeded random** (2026-09-17). Recipes fix the instruments per subject and choose randomly
  within them. The signals on the board (Sun differences, picture types) replace the random choices; if they don't
  arrive, cheaper ideas: weight by recent novelty per instrument, or by time since that instrument last appeared.

## Findings (settled 2026-09-17, so nobody re-asks)

- **Calibration frames and anomaly**: it depends on the instrument. Over a five-sol window, caltarget, sun-shot, and
  hardware frames are the high outliers on Mastcam-Z; raw anomaly is a garbage-and-hardware detector, and what it
  really exposes is that each instrument produces several picture *types* the metadata doesn't label. Details in
  `docs/research/embedding-experiment-2026-09-17.md`.
- **Global embeddings are flat on the Sun and Earth**; frame differences find events (a flare on 09-10). Same-framing
  sources need a difference signal, not an embedding.
- **SDO channels map temperature, not element.** Each AIA channel is mostly an iron ion line at a characteristic
  temperature; element distribution isn't reachable from AIA.
- **Perseverance product codes**: `ECM` is the processed image, `EBY` the raw Bayer frame (grey checkerboard look);
  both are published for many exposures and EBY is now dropped at extraction.
- **Wigglegrams**: align on the subject, set speed from near/far parallax spread, and pick one-subject close-ups;
  ground-looking mosaic tiles read as a sliding plane. Navcam eyes are 42 cm apart horizontally (not vertical stereo);
  A and B sides are redundant computers, not a stereo pair.
- **Earth is the weakest subject as built**; NOIRLab is fine as a deep-space filler but sits apart from the spacecraft
  sources; the explorer is the fastest feedback loop we have and should stay first-class as stages are added.
