# Tasks

Claim before starting: put your name or session in Owner and list the files you expect to touch.
Keep claims small and disjoint. Mark done with the commit hash. Newest at the top of each list.

## In progress

| Task | Owner | Files | Notes |
|---|---|---|---|

## Ready

| Task | Files | Notes |
|---|---|---|
| Newly-released treatment for delayed layers | `pipeline.py`, `sources/helioviewer.py` | Track the latest date per Helioviewer layer across manifests; when it jumps, that's a release. Pair with a realtime layer at the same capture time. |
| Sky-position reference lookup for deep space | new `references.py` | ESA meta has RA/Dec/FOV; MAST and ESA archives support cone search. |
| Helioviewer: SDO through the same adapter for time-matched comparisons | `sources/helioviewer.py` | SDO layers exist in Helioviewer (sourceIds 8-19); useful for same-instant comparisons with other spacecraft. |
| Feed storage growth (revisit around 2026-10-01 if the project continues) | `pipeline.py`, `.github/workflows/daily.yml` | Decided 2026-09-17 to leave feeds committed as-is: git packs them to about 216 KB/day; checkout grows 1.75 MB/day. Likely fix is a 30-day retention window in the tree. gzip rejected (no packed-size win, loses greppability). |
| APOD: migrate to the new endpoint before 2026-12-01 | `sources/apod.py`, `tests/fixtures/apod_*` | Legacy api.nasa.gov/planetary/apod is archived 2026-12-01. New: `https://science.nasa.gov/wp-json/wp/v2/apod-basic` (no key, returns a list; `url` is now the article permalink, image is `hdurl`). Keith's copy of the user guide: `docs/apod-feed-and-api-user-guide`. |
| Perseverance paging | `sources/perseverance.py` | Pull pages 0..N so a full sol is covered. |
| Ranker: per-instrument embedding anomaly | `rank.py`, `pipeline.py`, `pyproject.toml` | DINOv2-small on CPU; rolling window persisted under `data/embeddings/`. |
| Picker: vision model pick + caption | `pick.py`, `pipeline.py` | Decision on provider pending. |
| Index page: last N picks as a grid | `site/index.md`, `site/assets/css/style.css` | |

## Done

| Task | Commit |
|---|---|
| Skeleton: models, Perseverance source, stages, CLI, Jekyll site, workflows, docs | 27bb139..5b4f945 |
| Sources sdo, esa_webb, esa_hubble, epic, apod, hirise: fetch halves by main session, extractors by 4 parallel subagents | a1fb6a1 |
| Per-source freshness window | a1fb6a1 |
| Placeholder picker: weighted source, uniform instrument, no repeat of yesterday's source | d8c76a3 |
| Cleanup: per-source error isolation, chooser seam with derived-image support, rolling-window store, weights on sources, shared image cache env var | (this commit) |
