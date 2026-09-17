# Space image of the day — research context

Compiled 2026-09-17 morning for a one-day build. Facts marked **(verified)** come from web search today; **(from memory)** is Claude's training knowledge — treat as plausible, confirm with a curl before depending on it. See "Open questions" at the end.

## The project in one paragraph

Static site with a daily build (GitHub Actions) that pulls recent imagery from several space sources, ranks candidates for "interestingness" (per-instrument embedding anomaly → vision-LLM pick + caption), and publishes one image per day with an RSS feed. Stretch: sky-map inset (Aladin Lite) for astronomical targets; multispectral composite from per-filter frames; Rubin "new transient last night" source. Must-do is two sources + auto-pick + caption + RSS.

## Sources, ranked by ease

### Tier 1 — JSON/RSS feed, no key, small JPEGs, updates daily

| Source | Endpoint | Format / size | Cadence | Notes |
|---|---|---|---|---|
| **Mars rovers (Perseverance, Curiosity) raw images** (verified) | `https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&num=100&page=0&order=sol+desc` (swap `category=msl` for Curiosity) | JSON with `image_files.full_res` links, `camera.instrument`, `sol`, `date_taken_utc`, `sample_type` (filter out `Thumbnail`) | Hundreds of frames per sol, most days | Mastcam-Z frames are tagged per filter (e.g. 880 nm, 866 nm near-IR, monochrome). Perseverance full-res Mastcam-Z ≈ 1648×1200 (verified from feed sample). **This is the multispectral-composite source that needs no FITS.** JPEG sizes ≈ 100–500 KB each (from memory). |
| **SDO (sun) latest images** (verified) | `https://sdo.gsfc.nasa.gov/assets/img/latest/` — files like `latest_4096_0171.jpg`, `latest_1024_0193.jpg` etc. | JPEG, 512/1024/2048/4096 px squares; 4096 ≈ 2–5 MB (from memory) | Continuous, ~every 15 min | Many AIA wavelengths (94, 131, 171, 193, 211, 304, 335, 1600, 1700) + HMI. Trivially composited (each wavelength is a channel). Anomaly = flare/CME. |
| **Helioviewer API** (verified) | `https://api.helioviewer.org/v2/getJP2Image/?date=...&sourceId=...` ; Python wrapper `hvpy` (supersedes sunpy's HelioviewerClient) | JPEG2000, 4096×4096; also PNG screenshot/movie endpoints | Historical + latest | Same data as SDO above but queryable by time and instrument (SDO, SOHO, etc). Use if you want a specific time rather than "latest". |
| **NASA APOD** (verified) | `https://api.nasa.gov/planetary/apod?api_key=...` | JSON with `url`/`hdurl` | Daily | Curated, not raw — a baseline/fallback, not the point of the project. |
| **NASA EPIC (DSCOVR whole-Earth)** (from memory) | `https://api.nasa.gov/EPIC/api/natural/date/YYYY-MM-DD` → image names; images at `epic.gsfc.nasa.gov/archive/...` | PNG ~2048×2048, few MB | ~10–20/day | Colour is already composited. Earth, not "space", but pretty. |
| **HiRISE picture of the day (MRO orbiter)** (verified) | RSS: `https://www.uahirise.org/togo/rss.php` (one item per HiPOD) | 960×720 JPEG in the feed; full products are 1–2 gigapixel JPEG2000 — avoid | Roughly daily, curated | Feed was empty on one fetch and populated on another — treat as best-effort. Catalog JPEGs (map-projected, non-map) exist per observation on `hirise-pds.lpl.arizona.edu` but are large. |
| **ESA/Webb picture of the month** (verified) | `https://esawebb.org/images/potm/json/` → then `https://esawebb.org/images/{id}/api/json/` | Screen JPEGs at `cdn.esawebb.org/archives/images/screen/{id}.jpg`; originals are TIFF, tens of MB | Monthly | Curated press images. Same pattern for ESA/Hubble: `https://esahubble.org/images/{id}/api/json/`, screen JPEG at `cdn.esahubble.org/archives/images/screen/{id}.jpg`. ESA/Hubble originals average 44 MB, ~3267×2881 px (verified from a scrape). Metadata includes RA/Dec, field of view, constellation — **useful for the sky-map inset.** |
| **NOIRLab image of the week** (verified) | RSS `https://noirlab.edu/public/images/iotw/feed/` | JPEG | Weekly | Ground-based (Gemini, Blanco, and Rubin press images when they exist). |

A working reference for the ESA/SDO/NOIRLab patterns: `github.com/BarthPaleologue/SublimeSpaceBot` (a Bluesky bot; TypeScript) (verified).

### Tier 2 — feasible in a day but needs a real query or FITS

| Source | Access | Notes |
|---|---|---|
| **Rubin alerts** (verified) | Public alert stream since 2026-02-24 via 7 brokers: ALeRCE, AMPEL, ANTARES, Babamul, Fink, Lasair, Pitt-Google. Fink has a REST API (`/api/v1/...`) and a "data transfer" service; ALeRCE has an API + Jupyter notebooks that fetch alerts *and image cutouts*; Lasair filters with SQL. | Alerts carry small difference-image cutouts (postage stamps), not pretty wide-field frames — full LSST images sit under a proprietary period. So the product is "brightest new transient last night + where it is in the sky", not a Rubin picture. ~800k alerts/night at start, up to 7M eventually. Broker docs are written for astronomers; budget an hour for the first working query. |
| **JWST / Hubble science data via MAST** (partly verified) | `astroquery.mast.Observations.query_criteria(obs_collection="JWST", t_obs_release=[...])` etc. Data appears in MAST within hours of downlink (verified). | Products are FITS (`_i2d.fits` for calibrated images), typically tens to hundreds of MB each (from memory). MAST observation tables include a `jpegURL` preview column (from memory — **verify**); if that holds, you get a JPEG preview without touching FITS. `jwst_mast_query` (spacetelescope GitHub) is a helper for bulk queries. Proprietary periods mean "public today" ≠ "taken yesterday". |
| **ESA Hubble archive** (verified) | `astroquery.esa.hubble` — synced with MAST | Same FITS story. |

### Tier 3 — not a day-one source

| Source | Why not |
|---|---|
| **LRO / LROC (lunar orbiter)** (verified) | Data goes to PDS in bulk releases; browse products are pyramidal TIFFs; NAC frames are 5064 px wide swaths. There's a thumbnail browser at `data.lroc.im-ldi.com` (LROC team is now at Intuitive Machines) and a featured-image page, but no daily JSON feed found. |
| **BepiColombo (Mercury)** (verified) | Transfer module separated 2026-09-03; orbit insertion November 2026; the science camera (SIMBIO-SYS) only operates in orbit. Cruise imagery was from 1024×1024 B&W monitoring cameras, released ad hoc into ESA's Planetary Science Archive (within ~10 days). **Revisit in December 2026** — could become a great source. |
| Other orbiters (Juno/JunoCam, Cassini archive, Mars Express VMC) (from memory) | JunoCam raw frames need de-striping/stitching; Cassini is archival; Mars Express VMC posts to Flickr. All doable later, none day-one. |

## Other agencies (verified unless noted)

- **ESA**: esahubble.org / esawebb.org JSON per image (above); Planetary Science Archive (PSA) for mission data — `astroquery.esa.*` modules exist; ESA's public image site has RSS.
- **NOIRLab** (NSF): RSS above; hosts Rubin press releases.
- **JAXA / ISRO / CNSA** (from memory): no comparable public feeds found in this pass; skip.

## API keys

- **api.nasa.gov** (verified): sign-up is a web form (name + email); the key is shown immediately and emailed. No approval step. Registered key = 1,000 req/hr; `DEMO_KEY` = 30/hr and 50/day per IP. Only needed for APOD/EPIC/mars-photos on api.nasa.gov; the `mars.nasa.gov/rss/api` raw feed and SDO/Helioviewer/ESA/HiRISE/NOIRLab need **no key**.
- **MAST** (from memory): anonymous access for public data; a MyST token only for proprietary data.
- **Rubin brokers** (verified partially): alert data is public; some broker APIs may want a free account for stream subscriptions — the REST/notebook query paths appear open.

## Formats and sizes (approximate)

| Thing | Pixels | Size |
|---|---|---|
| Mars rover full-res JPEG | ~1600×1200 | 100–500 KB |
| SDO latest JPEG | 1024 / 2048 / 4096 sq | ~0.3 / 1 / 2–5 MB |
| Helioviewer JP2 | 4096×4096 | few MB |
| HiRISE feed JPEG | 960×720 | <1 MB |
| ESA Hubble/Webb screen JPEG | ~1280 wide | <1 MB; originals TIFF avg 44 MB |
| JWST `_i2d.fits` | varies | tens–hundreds of MB |
| Rubin alert cutout | ~30×30 px | tiny |

Implication: use each source's JPEG/PNG previews for ranking and display; never store raw. For a GitHub Actions daily build, a few hundred JPEGs at <1 MB each and CPU embeddings is comfortably within free-tier minutes (from memory — verify job time on first run).

## Python libraries

- **astropy** — FITS I/O, WCS, `astropy.visualization.make_lupton_rgb` for 3-band composites, stretches (from memory)
- **astroquery** — MAST (`astroquery.mast`), ESA archives (`astroquery.esa.hubble`, `.esa.*`) (verified)
- **sunpy** + **hvpy** — SDO/Helioviewer; sunpy `Map` handles AIA colour tables and coordinate frames (verified for hvpy; sunpy Map from memory)
- **reproject** — reproject one image onto another's WCS for aligned composites (from memory)
- **pdr** (Planetary Data Reader) / **planetarypy** — read PDS3/PDS4 products if you ever touch LROC/HiRISE raw (from memory)
- **glymur** or **Pillow** with OpenJPEG — JPEG2000 decode for Helioviewer/HiRISE (from memory)
- **feedparser** — RSS sources; **httpx/requests** for JSON
- Embeddings: **timm** or **transformers** for DINOv2 / CLIP on CPU (from memory)

## Multispectral composites — how

Two flavours, both day-sized:

1. **Already-registered channels** (SDO, Mastcam-Z filter sets): frames of the same scene at different wavelengths from the same pointing; stack as R/G/B with a stretch. No alignment needed for SDO; Mastcam-Z filter frames are taken seconds apart from the same pose, so feature-matching alignment (ORB + homography) covers residual shift. Pick channel-to-colour mapping by hand (e.g. 304/171/193 for the sun; near-IR/red/blue for Mars false colour).
2. **FITS with WCS** (JWST/Hubble): `reproject` each band onto a common WCS, then `make_lupton_rgb` or per-band asinh stretch. Heavier; keep for a later day unless the `jpegURL` preview turns out to be enough.

## Sky-map inset

**Aladin Lite** (from memory): embeddable JS sky viewer, takes RA/Dec + FOV, pans over a real survey. ESA Hubble/Webb JSON gives RA/Dec/FOV directly; Rubin alerts carry RA/Dec. Not applicable to Mars/sun images.

## Ranking pipeline (design, not research)

- Per-instrument rolling window (~7–30 days) of embeddings; score = distance from window centroid (DINOv2 or CLIP image embeddings).
- Filter obvious garbage before ranking: thumbnails, near-uniform images (calibration frames), failed downloads.
- Top-N per source → vision-LLM picks one and writes the caption. Also handles "is this actually interesting" precision.
- Cold start: backfill ~7 days of history per source on first run.

## Open questions to resolve in the research window (≤ 5 min each)

1. `curl` the Mars raw feed — confirm fields and that `order=sol+desc` gives yesterday's sol.
2. `curl` an SDO latest JPEG — confirm URL pattern and size.
3. One Fink or ALeRCE query returning last-night alerts with RA/Dec — if this fights you at 10:30, cut Rubin.
4. Does MAST's observation table really expose a JPEG preview URL? If yes, JWST becomes Tier 1.
5. GitHub Actions job time with the embedding step — measure on first run.
