# Tasks

Actionable work, grouped by theme. Claim before starting: put your name or session in Owner and list the files you
expect to touch; keep claims small and disjoint. Ideas that aren't ready to be tasks live in `docs/IDEAS.md`.
The build-day timeline is in `NOTES.md`; what's done is in `git log`.

## In progress

| Task | Owner | Files | Notes |
|---|---|---|---|

## Day 2, in order (Keith's ordering, 2026-09-17 debrief)

| Task | Files | Notes |
|---|---|---|
| Perseverance paging in the daily fetch | `sources/perseverance.py` | Page 0 alone missed the sol's Mastcam-Z colour frames on 2026-09-17; the wigglegram search leans on the committed survey pages, which go stale. Fetch pages 0..3. Highest priority: we are missing frames. |
| Picture-type labels per instrument | `publish.py` (explorer), new `labels.py`, `data/reference/` | Cluster embeddings per instrument (DINOv2 or anything), show clusters in the explorer, Keith names them once, then rank within type. Should be easy, and unlocks colour calibration (finding caltarget frames) and better picks. |
| Notation explainers on the remaining Sun cards | `data/reference/instruments/sun.yaml` | Follow the AIA pattern: ion, temperature, why a wavelength isolates it. |
| STEREO-A beacon on the Sun page | `sources/stereo.py`, `pipeline.py` | Fresher than Helioviewer's 3-day lag. Latest-style URLs need a cache key with Last-Modified, or a fetch stage that saves the bytes under a dated name. |
| More from MRO: HiRISE catalog, and CTX or MARCI if reachable | `sources/hirise.py`, new sources | Keith would love more HiRISE. HiPOD is one a day; every observation has a browse JPEG in the catalog (needs research on a "latest releases" listing). MARCI's weekly weather report is video-first; CTX is PDS-only so far. |
| End of day 2, could be big: Sun difference detector as the SDO chooser | `digest.py`, new `signals.py` | Frame differences at native cadence per channel, validated 2026-09-17 (found a flare). Then pair an AIA eruption with the LASCO CME hours later. Needs a worked example of what the "story" is before it's more than a chooser. |

## Learning UI (a cluster, not yet scheduled)

| Task | Files | Notes |
|---|---|---|
| Vehicle sketch with the active instrument lit | `site/`, cards | SVG per spacecraft on the post. Reference diagrams for Perseverance, Curiosity, MRO, and GOES-19 are under `data/reference/sketches/` with sources; SDO and the rest still to collect. Goes with the next row. |
| Where the vehicle is in the solar system | `site/`, new data | Position relative to Earth and the Sun. Ephemerides via JPL Horizons would do it. Destination: the Mass Effect styled mission-select screen in IDEAS, clickable spacecraft and ground telescopes. |

## Digest and site

| Task | Files | Notes |
|---|---|---|
| Phobos and Deimos transits as a treat | `sources/perseverance.py`, `digest.py` | Keith: would be amazing. ND solar-filter frames (L7/R7) are dropped at extraction today; keep them as a separate pool, detect a transit as a bite out of the disc (or from the sequence id on transit days), and give it a panel when it happens. |
| Earth needs a reason to exist (research task) | `digest.py`, `sources/gibs.py` | Keith 2026-09-17: least interesting subject as built, and it isn't obvious what would be interesting. Candidates: GIBS specialty layers by date (fires, sea surface temperature, night lights), "Earth from far away" only, or Earth one day in five. Start by browsing GIBS layers. |
| Storage growth: feeds, Helioviewer previews, digest images | `pipeline.py`, `publish.py`, `.github/workflows/daily.yml` | Committed growth today: feeds about 216 KB/day packed (1.75 MB/day in the checkout), Helioviewer previews about 6 MB/day, digest images 1-3 MB/day. Options: retention windows in the tree, git-lfs, S3 (possibly with DVC). Decide before it matters, around 2026-10-01 if the project continues. gzip rejected (no packed-size win, loses greppability). |

## Sources

| Task | Files | Notes |
|---|---|---|
| NASA GIBS WMS (Earth, hundreds of layers) | `sources/gibs.py` | Date-addressable GetMap PNGs; see `docs/research/feed-access-2026-09-17.md`. Keith: could be cool; the likely answer to the Earth research task. |
| SDO through Helioviewer for time-matched comparisons | `sources/helioviewer.py` | SDO layers exist there (sourceIds 8-19); same-instant frames beside other spacecraft. |
| Newly-released treatment for delayed layers | `pipeline.py`, `sources/helioviewer.py` | Track each layer's newest date across manifests; a jump is a release (Solar Orbiter lags 20 months). Pair with a realtime layer at the same capture time. |
| Sky-position reference lookup for deep space | new `references.py` | ESA meta carries RA/Dec/FOV; MAST and ESA archives support cone search, so "older Hubble images of this field" is a query. |
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
| Before 2026-12-01 | APOD: migrate to the new endpoint | `sources/apod.py`, `tests/fixtures/apod_*` | Legacy `api.nasa.gov/planetary/apod` is archived then. New: `https://science.nasa.gov/wp-json/wp/v2/apod-basic` (no key, returns a list, `url` is the article permalink and the image is `hdurl`). Keith's local copy of the guide (not committed): `docs/local/apod-feed-and-api-user-guide.md`; the source is https://schlotterer.notion.site/APOD-Feed-And-API-User-Guide-39697d8747c38015a53edfdde76d4f5e. Could also backfill a week. |
| December 2026 | BepiColombo as a source | new source | Orbit insertion 2026-11-21, science from 2027-04; flyby images so far were press releases. |

## Done

Everything shipped on 2026-09-17 is in `git log` and the timeline in `NOTES.md`. Headlines: 11 sources, explorer pages
with a week of history, subject-of-the-day digest with instrument cards on every panel, a wigglegram panel, an
unattended daily job, and three research notes under `docs/research/`.
