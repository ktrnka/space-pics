# Tasks

Claim before starting: put your name or session in Owner and list the files you expect to touch.
Keep claims small and disjoint. Mark done with the commit hash. Newest at the top of each list.

## In progress

| Task | Owner | Files | Notes |
|---|---|---|---|

## Ready

| Task | Files | Notes |
|---|---|---|
| Perseverance paging in the daily fetch | `sources/perseverance.py` | Page 0 alone missed the sol's Mastcam-Z colour frames today; the wigglegram search currently leans on the committed survey pages, which will go stale. Fetch pages 0..3. |
| Wigglegram selection: prefer one-subject close-ups | `wiggle.py` | Keith's verdict: a single rock mid-frame with ground before and behind is ideal; survey mosaics are not. Navcam horizon pairs still untested. |
| Day 2, first: Sun difference detector as the SDO chooser | `digest.py`, new `signals.py` | Frame differences at native cadence per channel; validated 2026-09-17 (found a flare). Pair AIA eruptions with LASCO CMEs hours later. |
| Day 2, second: picture-type labels per instrument | `publish.py` (explorer), new `labels.py`, `data/reference/` | Cluster DINOv2 embeddings per instrument, show clusters in the explorer, Keith names them once; then rank within type. |
| Day 2, third: vehicle sketch with the active instrument lit | `site/`, cards | SVG per spacecraft on the post; extension of where-in-the-universe. |
| Digest panels grouped by spacecraft | `templates/digest.md.j2` | |
| Notation explainers on the remaining Sun cards | `data/reference/instruments/sun.yaml` | Follow the AIA pattern (ion, temperature, why a wavelength isolates it). |
| Earth: a different angle or a smaller share of the rotation | `digest.py`, `sources/gibs.py` | See IDEAS: GIBS specialty layers, or Earth one day in five. |
| Helioviewer preview growth | `publish.py` | Local previews under `site/debug/img/helioviewer/` cost about 6 MB/day committed. Prune to the last N days, or downscale to 256 px, before it matters. |
| Source: NASA GIBS WMS (Earth, many layers) | `sources/gibs.py` | Date-addressable GetMap PNGs; pick a few layers (true colour, night lights, sea surface temperature). |
| Source: STEREO-A beacon (fresher than Helioviewer's 3-day lag) | `sources/stereo.py` | latest-style URLs; needs the Last-Modified cache key (see research note). |
| Newly-released treatment for delayed layers | `pipeline.py`, `sources/helioviewer.py` | Track the latest date per Helioviewer layer across manifests; when it jumps, that's a release. Pair with a realtime layer at the same capture time. |
| Sky-position reference lookup for deep space | new `references.py` | ESA meta has RA/Dec/FOV; MAST and ESA archives support cone search. |
| Helioviewer: SDO through the same adapter for time-matched comparisons | `sources/helioviewer.py` | SDO layers exist in Helioviewer (sourceIds 8-19); useful for same-instant comparisons with other spacecraft. |
| Feed storage growth (revisit around 2026-10-01 if the project continues) | `pipeline.py`, `.github/workflows/daily.yml` | Decided 2026-09-17 to leave feeds committed as-is: git packs them to about 216 KB/day; checkout grows 1.75 MB/day. Likely fix is a 30-day retention window in the tree. gzip rejected (no packed-size win, loses greppability). |
| APOD: migrate to the new endpoint before 2026-12-01 | `sources/apod.py`, `tests/fixtures/apod_*` | Legacy api.nasa.gov/planetary/apod is archived 2026-12-01. New: `https://science.nasa.gov/wp-json/wp/v2/apod-basic` (no key, returns a list; `url` is now the article permalink, image is `hdurl`). Keith's copy of the user guide: `docs/apod-feed-and-api-user-guide`. |

## Done

| Task | Commit |
|---|---|
| Wigglegram panel in the Mars digest (guarded; Mastcam-Z colour pairs, 8-40 px parallax spread) | 15:30 merge of branch `wigglegram` |
| Subject-of-the-day digest with rotation and per-subject recipes; instrument cards (3 subagents); readable metadata; EBY/ND filtering | (13:50 commits) |
| Sources goes (GOES-19 GeoColor) and noirlab; Curiosity sequence ids | (12:25 commits) |
| Sources helioviewer (29 layers) and curiosity; explorer pages with sequence and time-grid layouts; week-long survey folded in | 2a8d9b8 and this commit |
| Skeleton: models, Perseverance source, stages, CLI, Jekyll site, workflows, docs | 27bb139..5b4f945 |
| Sources sdo, esa_webb, esa_hubble, epic, apod, hirise: fetch halves by main session, extractors by 4 parallel subagents | a1fb6a1 |
| Per-source freshness window | a1fb6a1 |
| Placeholder picker: weighted source, uniform instrument, no repeat of yesterday's source | d8c76a3 |
| Cleanup: per-source error isolation, chooser seam with derived-image support, rolling-window store, weights on sources, shared image cache env var | (this commit) |
