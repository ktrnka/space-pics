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

## Candidates not yet built (see research doc for endpoints)

- **sdo**: `https://sdo.gsfc.nasa.gov/assets/img/latest/latest_{1024,2048,4096}_{0171,0193,0304,...}.jpg`. Verified live; 1024 px files are 140 to 210 KB. One frame per wavelength per fetch, so `source_id` must include the fetch time. No feed to save; `fetch_feed` could return a small JSON manifest of URLs plus `Last-Modified` headers.
- **esa_hubble / esa_webb**: `https://esawebb.org/images/potm/json/` then `/images/{id}/api/json/`. Has RA/Dec and FOV for a sky-map inset.
- **epic**: `https://api.nasa.gov/EPIC/api/natural/date/YYYY-MM-DD` with `NASA_API_KEY`.
- **apod**: `https://api.nasa.gov/planetary/apod`. Curated; fallback only.
