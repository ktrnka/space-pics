# Tasks

Actionable work, grouped by theme. Claim before starting: put your name or session in Owner and list the files you
expect to touch; keep claims small and disjoint. Ideas that aren't ready to be tasks live in `docs/IDEAS.md`.
The build-day timeline is in `NOTES.md`; what's done is in `git log`.

## In progress

| Task | Owner | Files | Notes |
|---|---|---|---|

## Day 2, in order

| Task | Files | Notes |
|---|---|---|
| Sun difference detector as the SDO chooser | `digest.py`, new `signals.py` | Frame differences at native cadence per channel, validated 2026-09-17 (found a flare, see `docs/research/embedding-experiment-2026-09-17.md`). Then pair an AIA eruption with the LASCO CME hours later. |
| Picture-type labels per instrument | `publish.py` (explorer), new `labels.py`, `data/reference/` | Cluster DINOv2 embeddings per instrument, show clusters in the explorer, Keith names them once, then rank within type. Also the home for "which frames are calibration/hardware/sun". |
| Perseverance paging in the daily fetch | `sources/perseverance.py` | Page 0 alone missed the sol's Mastcam-Z colour frames on 2026-09-17; the wigglegram search leans on the committed survey pages, which go stale. Fetch pages 0..3. |
| Vehicle sketch with the active instrument lit | `site/`, cards | SVG per spacecraft on the post; the where-in-the-universe idea made concrete. |

## Digest and site

| Task | Files | Notes |
|---|---|---|
| Wigglegram selection: prefer one-subject close-ups | `wiggle.py` | Keith's verdict 2026-09-17: a single rock mid-frame with ground before and behind is ideal; survey mosaics read as a sliding plane. Navcam horizon pairs untested. |
| Digest panels grouped by spacecraft, then instrument | `templates/digest.md.j2` | Matters once a subject has several spacecraft per day (Sun already does). |
| Earth: a different angle or a smaller share of the rotation | `digest.py`, `sources/gibs.py` | Keith 2026-09-17: least interesting subject as built. Options: GIBS specialty layers by date (fires, sea surface temperature, night lights), "Earth from far away" only, or Earth one day in five. |
| Notation explainers on the remaining Sun cards | `data/reference/instruments/sun.yaml` | Follow the AIA pattern: ion, temperature, why a wavelength isolates it. |
| Helioviewer preview growth | `publish.py` | `site/debug/img/helioviewer/` costs about 6 MB/day committed. Prune to the last N days or downscale to 256 px before it matters. |

## Sources

| Task | Files | Notes |
|---|---|---|
| NASA GIBS WMS (Earth, hundreds of layers) | `sources/gibs.py` | Date-addressable GetMap PNGs; see `docs/research/feed-access-2026-09-17.md`. The likely fix for the Earth problem above. |
| STEREO-A beacon (fresher than Helioviewer's 3-day lag) | `sources/stereo.py`, `pipeline.py` | Latest-style URLs need a cache key with Last-Modified, or a fetch stage that saves the bytes under a dated name. |
| SDO through Helioviewer for time-matched comparisons | `sources/helioviewer.py` | SDO layers exist there (sourceIds 8-19); same-instant frames beside other spacecraft. |
| Newly-released treatment for delayed layers | `pipeline.py`, `sources/helioviewer.py` | Track each layer's newest date across manifests; a jump is a release (Solar Orbiter lags 20 months). Pair with a realtime layer at the same capture time. |
| Sky-position reference lookup for deep space | new `references.py` | ESA meta carries RA/Dec/FOV; MAST and ESA archives support cone search, so "older Hubble images of this field" is a query. |
| More HiRISE | `sources/hirise.py` | HiPOD is one a day; every observation has a browse JPEG in the catalog. Needs research on a "latest releases" listing. |
| NOIRLab per-image credit | `sources/noirlab.py` | The RSS carries no facility/photographer line; the image page does. Fetch it for the newest few, as ESA does. |

## Code health (from the 2026-09-17 review)

| Task | Files | Notes |
|---|---|---|
| Decide the fate of the single-image pick path | `pipeline.pick`, `models.Pick`, `publish.write_post`, `post.md.j2`, `cli pick` | Nobody runs it since the digest. Keep as a documented manual escape hatch (then fix its raw source/instrument ids in the template) or delete it. |
| Source declares its explorer layout | `sources/base.py`, `publish.gallery_context` | Layout is chosen by `subject == "Mars"` / `name == "sdo"` checks; a `gallery_layout` attribute keeps new sources out of publish.py. |
| Untangle the digest/publish import cycle | `digest.py`, `publish.py`, `store.py` | `survey_candidates` lives in publish and digest imports it inside a function; move it to store. |
| One shared "Mastcam-Z colour frame" predicate | `digest.py`, `wiggle.py` | Two different filters for the same idea. |
| Card fields nobody reads | `reference.Card`, `data/reference/README.md` | `picture_types` and `confidence` are filled on every card but unused; surface `confidence` on posts or drop both. |

## Dated maintenance

| When | Task | Files | Notes |
|---|---|---|---|
| Around 2026-10-01, if the project continues | Feed storage growth | `pipeline.py`, `.github/workflows/daily.yml` | Decided 2026-09-17 to leave feeds committed: git packs them to about 216 KB/day, checkout grows 1.75 MB/day. Likely fix: a 30-day retention window in the tree. gzip rejected (no packed-size win, loses greppability). |
| Before 2026-12-01 | APOD: migrate to the new endpoint | `sources/apod.py`, `tests/fixtures/apod_*` | Legacy `api.nasa.gov/planetary/apod` is archived then. New: `https://science.nasa.gov/wp-json/wp/v2/apod-basic` (no key, returns a list, `url` is the article permalink and the image is `hdurl`). Keith's copy of the guide: `docs/apod-feed-and-api-user-guide`. Could also backfill a week. |
| December 2026 | BepiColombo as a source | new source | Orbit insertion 2026-11-21, science from 2027-04; flyby images so far were press releases. |

## Done

Everything shipped on 2026-09-17 is in `git log` and the timeline in `NOTES.md`. Headlines: 11 sources, explorer pages
with a week of history, subject-of-the-day digest with instrument cards on every panel, a wigglegram panel, an
unattended daily job, and three research notes under `docs/research/`.
