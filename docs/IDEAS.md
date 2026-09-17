# Ideas

A parking lot for things noticed while looking at the output. Not commitments. When one is worth exploring,
move it to `docs/TASKS.md` with a file set so an agent can take it in a worktree.

Format: one bullet per idea, with enough context that someone who didn't see the trigger can evaluate it.
Add a date and where the idea came from (which debug page, which pick).

## Image processing

- **Colour-correct Mastcam-Z frames against the calibration target** (2026-09-17, from the perseverance debug page).
  The raw-feed browse JPEGs are not calibrated; official "natural colour" and "white-balanced" releases are
  produced by the instrument team using the deck calibration target (grey rings, colour swatches, shadow post).
  Question to explore: can we find caltarget frames in the feed (fixed pointing, so mast az/el in the feed's
  `extended` block should identify them), estimate per-channel gains from the known swatch reflectances, and apply
  them to same-sol frames? Limits: 8-bit JPEG browse products with unknown onboard processing, so "looks right",
  not science-grade.
- Use PR photos as training data for multi-spectral work, if we can match a PR photo to the sources (this way there's a little less guess and check for MS work)

- **Mastcam-Z near-IR decorrelation stretch** (2026-09-17, Keith's gallery notes). The right eye's 800-1022 nm filters
  target iron-mineral absorption features; the team publishes band-ratio and decorrelation-stretch composites that make
  rock composition differences visible. Same sequence, same eye, no alignment needed (filter wheel cycles in seconds
  from a fixed pointing). Day-sized and would actually show something.
- **Exclude or feature the ND solar frames** (2026-09-17). L7 (590 nm, ND6) and R7 (880 nm, ND5) are Sun shots for
  dust opacity and moon transits: a small disc on black. Either filter them from picking or make transits a treat.
- **Calibration frames and anomaly scores** (2026-09-17). Settled: over a five-sol window, caltarget, sun-shot, and
  hardware frames are the HIGH outliers (Keith's guess). Raw anomaly is a garbage/hardware detector; see
  docs/research/embedding-experiment-2026-09-17.md for what to do with that.
- **Navcam love** (2026-09-17, Keith). Navcam frames deserve a fair share; don't let ranking bury them.
- **SDO channels are temperature, not element** (2026-09-17). Each AIA channel is mostly an iron ion line at a
  different temperature; the 211/193/171 composite is already a temperature map. Element mapping isn't reachable
  from AIA. Other composites worth trying: 304/171/193, 094/335/193 for flares.
- **Raw Webb via MAST to tune composites** (2026-09-17, Keith). Use ESA's finished picture-of-the-month images as
  targets for a composite pipeline over the underlying per-filter frames. FITS-sized; later day.
- **Tomorrow's snapshot for calibration**: the debug galleries are the fastest feedback loop we have; keep them
  first-class as stages are added (ranker scores, shortlist, composite previews).

## Sources

- **More HiRISE** (2026-09-17, Keith): the HiPOD is one a day, but every observation has a browse JPEG in the
  catalog; a "latest releases" page scrape could yield dozens. Needs research.
- **APOD backfill** (2026-09-17): the new endpoint returns a list, so a migration could pull the last week rather
  than one item.

- Perseverance paging beyond the first 100 frames so a whole sol is covered.

## Learning layer (2026-09-17, Keith, after the explorer review)

- **Connect each image to its instrument and spacecraft.** A card per (spacecraft, instrument): what it is, what it
  sees (wavelengths, field, resolution), why it exists, a Wikipedia link. Shown on every post and explorer group.
  Also the natural home for the "picture types" this instrument produces once we've labelled them.
- **Vehicle sketch with the active sensor highlighted.** A simple SVG per spacecraft, the instrument lit up on the
  post; an extension of where-in-the-universe. Later day; the cards come first.
- **Human-readable metadata on the image page.** Parse `meta` into labelled lines (sol, local Mars time, mast
  pointing, filter and wavelength, lag since capture) instead of raw keys.
- **Rover anomaly**: no single signal; for same-framing sources (Sun, Earth) difference-from-average works; for rovers,
  label picture types first.

## Subjects

- **Earth is the least interesting subject as built** (2026-09-17, Keith): great high-res satellite imagery sites already
  exist. Angles that could earn its place: GIBS specialty layers by date (fires, sea surface temperature, night lights,
  aerosols), "Earth from far away" only (EPIC, and any spacecraft looking back), or dropping Earth to one day in five.
- **Build our own SUVI composite** (2026-09-17, Keith): SUVI has 94/131/171/195/284/304 like AIA; a 3-channel composite
  would sit beside AIA's 211/193/171 for a two-spacecraft comparison.
- **Sun story arcs**: eruption on the disc (AIA 304/171) then the CME in LASCO hours later; a difference-signal detector
  could pair them automatically.

## Site

- **Wiggle stereo (wigglegram) from stereo pairs** (2026-09-17, Keith). Navcam and Mastcam-Z left/right frames of the
  same sequence taken seconds apart: alternate them in an animated image to fake depth, an old trick that works well.
  (A and B sides are redundant computers, not a stereo pair; the pair is left/right.)
- **Digest panels grouped by spacecraft, then instrument** (2026-09-17, Keith). Headers per vehicle would read better
  than a flat panel list once a subject has several spacecraft.
- **Explain spectroscopic notation once** (2026-09-17, Keith): "Fe XIV" and "211 Å" mean nothing to a newcomer; the
  AIA card now has a plain-English paragraph, and the pattern should carry to other instruments (ion, temperature,
  why a wavelength isolates it).
- **Show the Earth date beside the sol** (2026-09-17, Keith). Done on sol headers; the general point stands: Mars
  and Earth time both matter, keep both visible.
- **NOIRLab sits apart** (2026-09-17, Keith): interesting but not closely related to the spacecraft sources; fine as
  a deep-space filler, don't build around it.
- Per-instrument debug galleries for every source, linked from a debug index (exists for perseverance; keep it as sources are added).
- User interface theme inspired from classic space UIs, or actually maybe Mass Effect? It'd be pretty dope to have a ME theme
- Some sort of UI that shows where each spacecraft is, relative to earth-sol? Like the mission select screen

## Image selection

- **Picture types per instrument** (2026-09-17, Keith, from the anomaly page). Each instrument mixes several kinds of
  frame (rocks, hardware checks, calibration, sun, sky, raw Bayer) and the feed doesn't label them. Cluster embeddings
  per instrument, label clusters once by eye in the explorer, then rank within type. This is the real ranker.
- **Drop EBY (raw Bayer) products at extraction** (2026-09-17). They duplicate the ECM frame in worse form. Same check
  for Curiosity's id scheme.
- **Keepers noticed by eye** (2026-09-17): NAVCAM_LEFT sun frame; HMIIC day with three big sunspots; GOES GeoColor
  composites are far better than expected; CHEMCAM_RMI deserves a dedicated look.
- Pick weighting beyond the placeholder (2026-09-17). Today: fixed source weights, uniform instrument within source, avoid yesterday's source. Longer term the ranker + VLM should replace weights entirely; if not, ideas: weight by recent novelty per instrument, or by how long since that source last appeared.
- High outliers are probably calibration stuff. Possibly tune a range from an outlier detection model to select interesting stuff