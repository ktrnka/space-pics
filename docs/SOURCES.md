# Sources

One section per adapter. Record the endpoint, what the raw records look like, quirks, and what's in `meta`.
Research notes for candidate sources not yet built are in `space-image-of-the-day-research.md`.

## perseverance (`sources/perseverance.py`)

- Feed: `https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&order=sol desc&num=100&page=0`. No key.
- Quirk: the documented `order=sol+desc` breaks when the `+` is percent-encoded (the API 302s to an HTML page). Send a space instead.
- Quirk: the API caps a page at 100 items regardless of `num`. Paging (`page=1,2,...`) is not implemented yet.
- Raw fields used: `imageid`, `sol`, `date_taken_utc` (naive string, UTC), `sample_type` (`Full` or `Thumbnail`), `camera.instrument`, `camera.filter_name`, `image_files.{small,medium,large,full_res}`.
- Candidate mapping: `image_url` = `large` (1200 px JPEG), `preview_url` = `medium` (800 px). Thumbnails dropped. `filter_name` of `UNK` becomes `None`.
- `meta`: `sol`, `filter_name` (e.g. `ZCAM_R2_866NM`; Mastcam-Z filter sets are the multispectral composite source).
- Instruments seen: `MCZ_LEFT`, `MCZ_RIGHT`, `FRONT_HAZCAM_*`, `REAR_HAZCAM_*`, `NAVCAM_*`, and engineering cams. Hazcam and navcam frames are frequent and repetitive; ranking will need per-instrument handling.
- Curiosity (`category=msl`) returns "No more images" on this endpoint; not pursued.

## curiosity (`sources/curiosity.py`)

- Feed: `https://mars.nasa.gov/api/v1/raw_image_items/?order=sol desc&per_page=100&page=0&condition_1=msl:mission`. No key. The older `rss/api?category=msl` endpoint returns "No more images".
- Quirk: as with Perseverance, a literal `+` in `order` breaks the request; send a space.
- Quirk: `extended.url_list` is a single URL identical to `https_url` (2026-09-17), not a list of sizes; no smaller image, so `preview_url` = `image_url` (full-size JPEG). Consider making previews from the cached full image later.
- Quirk: `link` is feed-relative (`/raw_images/1639694`), so `source_page_url` is None.
- Raw fields used: `imageid`, `sol`, `instrument` (NAV_RIGHT_B, CHEMCAM_RMI, MAST_LEFT/RIGHT, MAHLI, FHAZ_*, RHAZ_*, MARDI), `date_taken` (ISO, Z), `https_url`, `is_thumbnail` (61 of 100 on the first page; dropped), `image_credit`, `extended.{mast_az,mast_el,lmst}`.
- Candidate mapping: `spacecraft` = Curiosity; `instrument` = raw string; title like "Curiosity NAV_RIGHT_B, sol 5017".
- `meta`: `sol`, `mast_az`, `mast_el` (strings as given), `lmst`. No sequence id yet; the imageid encodes one (e.g. `CCAM05016`), worth adding for the explorer.

## sdo (`sources/sdo.py`)

- Feed: directory listing HTML at `https://sdo.gsfc.nasa.gov/assets/img/browse/YYYY/MM/DD/` (about 1.2 MB). No key. Filenames are `YYYYMMDD_HHMMSS_SIZE_CHANNEL.jpg`, one per channel roughly every 1 to 15 minutes depending on channel. Use these, not `assets/img/latest/` (same URL, changing bytes).
- Quirk: each listing row repeats the filename in the href and the link text; the regex matches `href="..."` only.
- Quirk: the listing carries more channels than we show (`HMIB`, `HMIBC`, `HMID`, `HMIIF`, `HMII`, `211193171n`, `211193171rg`, `304211171`, `094335193`, `HMI171`, `4500`) and sizes 256/512/1024/2048/3072/4096. Only `CHANNELS` at size 1024 are kept before subsampling.
- Subsampling: per channel, the earliest frame in each 3-hour UTC bucket (`hour // 3`). About 11 channels x up to 8 slots per day; fewer on a partial day since the daily fetch runs once.
- Candidate mapping: `source_id` = the 1024 filename stem (e.g. `20260917_173710_1024_0171`); `instrument` = channel string; `preview_url` = the 1024 URL; `image_url` = same name with `_2048_` (present on the server at the same timestamps, not cross-checked against the listing). Titles: `SDO AIA 171 Å`, `SDO HMI intensitygram`, `SDO AIA 211/193/171 composite`.
- `meta`: `channel`, `size` (1024), `wavelength_angstrom` (int for numeric AIA channels, else None).
- `source_page_url` is fixed at `https://sdo.gsfc.nasa.gov/data/`.

## helioviewer (`sources/helioviewer.py`)

- One adapter, many spacecraft: SOHO (LASCO C2/C3, EIT), STEREO-A (EUVI, COR1, COR2), PROBA-2 SWAP, GOES (SUVI, CCOR-1), GONG H-alpha, MLSO KCor, Hinode XRT, Solar Orbiter (EUI FSI/HRI, SoloHI), PUNCH. Layers are listed in `LAYERS` with their Helioviewer `sourceId`; `getDataSources` shows every available layer and its latest date.
- Feed: a manifest, not a feed. `fetch_feed` calls `getClosestImage` once per layer for noon UTC today (cheap metadata: real frame date, native scale and size) and records the `takeScreenshot` URLs to use. About 29 requests, paced.
- Images: `takeScreenshot` renders a PNG server-side (about 700 KB at 1024 px). `imageScale = native_scale * native_width / size` fits the whole frame. Each is a render, so counts stay small: 29 previews and at most one display image per day.
- Lag varies by layer and is recorded in `meta.lag_days`. Observed 2026-09-17: GOES, LASCO, PROBA-2, GONG, KCor within minutes; STEREO-A 3 days; SOHO EIT and Hinode about 3 weeks; PUNCH a month; SoloHI 5 months; Solar Orbiter EUI 20 months. `captured_at` is the real frame date, so freshness (3 days) drops the laggards; the "newly released" treatment for delayed layers is future work.
- Candidate mapping: `spacecraft` = the vehicle; `instrument` = "spacecraft instrument" (e.g. "SOHO LASCO C2") so galleries group per detector; `source_id` = sourceId plus frame timestamp; `source_page_url` = helioviewer.org at that date.
- `meta`: `helioviewer_source_id`, `measurement`, `native_scale_arcsec_px`, `native_width`, `lag_days`.
- No rate limit published; be gentle, it is a shared public service.

## epic (`sources/epic.py`)

- Feed: `https://api.nasa.gov/EPIC/api/natural` with `NASA_API_KEY` (`DEMO_KEY` works at low volume). Returns the most recent available day's images (10 to 20), not a chosen date.
- Quirk: the latest available day lags real time by several days (4 days observed on 2026-09-17); `freshness_days = 10`.
- Quirk: the image URL is built from the record's `date`, not `identifier` (they encode slightly different timestamps). Pattern: `https://epic.gsfc.nasa.gov/archive/natural/YYYY/MM/DD/jpg/{image}.jpg` (about 1080 px, 200 KB). `thumbs/` is 5 KB, `png/` is 2048 px and several MB; use neither.
- Raw fields used: `identifier`, `image`, `version`, `date` (naive, UTC), `centroid_coordinates.{lat,lon}`.
- Candidate mapping: `image_url` = `preview_url`; single instrument `epic_natural`; title like "Earth from DSCOVR, centred on 7.0°N 165.7°E".
- `meta`: `centroid_lat`, `centroid_lon`, `version`.

## apod (`sources/apod.py`)

- Feed: `https://api.nasa.gov/planetary/apod`. Needs `NASA_API_KEY`. Curated, so a fallback rather than the point.
- Quirk: a single JSON object, not a list. `media_type` is `image` or `video`; video days extract to nothing.
- Quirk: `copyright` is optional and formatted for display with embedded newlines; collapsed to one line for `credit`, falling back to "NASA APOD".
- Candidate mapping: `source_id` = the date string; `captured_at` = that date at 00:00 UTC; `image_url` = `preview_url` = `url` (the standard size). `hdurl` can be a multi-MB original and only goes in `meta`. `source_page_url` = `https://apod.nasa.gov/apod/ap{YYMMDD}.html`.
- `meta`: `explanation`, `hdurl`.

## hirise (`sources/hirise.py`)

- Feed: RSS 0.91 at `https://www.uahirise.org/togo/rss.php`. No key. Empty on one research fetch and populated on another; best effort.
- Shape seen 2026-09-17: a channel with a `pubDate` and exactly one item (title, link, description). No per-item `pubDate`.
- Quirk: `captured_at` uses the item's pubDate if present, else the channel's (roughly publish time, not observation time), parsed with `email.utils.parsedate_to_datetime`. Items with neither are dropped.
- Quirk: the image URL and a credit line live inside the description's HTML; the `<img src>` is regexed out and the credit is a fixed constant.
- Candidate mapping: `source_id` = last path segment of the link (observation id like `ESP_065221_2055`); `image_url` = `preview_url` = the feed's small JPEG (about 960x720); title has the leading "HiPOD: " stripped.
- `meta`: `description` (tags stripped).

## esa_webb / esa_hubble (`sources/esa.py`)

- One class, `EsaSource`, instantiated twice: `esa_webb` (`https://esawebb.org`, list `potm`) and `esa_hubble` (`https://esahubble.org`, list `potw`). No key. `freshness_days = 45`.
- List feed: `{host}/images/{potm|potw}/json/`, the 20 most recent releases, each with a `formats_url` map of every image size (originals are TIFF: never use). Per-image API: `{host}/images/{image_id}/api/json/` (image id like `potm2608a`, not the release id `potm2608`) carries RA/Dec, FOV, credit, sometimes an object name. `fetch_feed` saves both in one document, `{"list": [...], "images": {image_id: {...}}}`, with detail for the newest 3 only.
- Quirk: a release can have no still image (a before/after comparison slider has `image: null`). Skipped.
- Quirk: the detail JSON is AVM (Astronomy Visualisation Metadata) with dotted keys (`Spatial.ReferenceValue`, `Spatial.ReferenceDimension`, `Spatial.Scale`, `Subject.Name`), and its text fields are the Python `repr()` of a bytes object baked into the JSON string (e.g. `"b'ESA/Webb, NASA & CSA'"`). Decoded with `ast.literal_eval(...).decode()`.
- Quirk: the Hubble POTW list's newest entry on 2026-09-17 is dated 2025-12-29; the feed is stale or the series paused. Not compensated for.
- Candidate mapping: `instrument` = `webb` or `hubble`; `image_url` = `formats_url["screen"]` (about 1280 px); `preview_url` = `formats_url["screen640"]`; `credit` from the detail when present, else a fixed agency credit; `source_page_url` = `{host}/images/{image_id}/`.
- `meta`: `release_id`, `ra`, `dec` (decimal degrees), `fov` (`width_arcmin`, `height_arcmin`, computed from dimension x scale), `constellation` (regexed from the free-text description; often None), `object` (from `Subject.Name`), `description` (first sentence). All None for releases without a detail record.

## Candidates not yet built (see research doc for endpoints)

