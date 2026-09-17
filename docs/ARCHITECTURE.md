# Architecture

## Stages

```
fetch      network   source feeds  ->  data/feeds/<source>/<date>.json        (saved verbatim)
extract    offline   saved feed    ->  data/candidates/<source>/<date>.jsonl   (list of Candidate)
download   network   candidates    ->  data/images/<hash>.<ext>                (gitignored cache keyed by URL hash)
digest     offline*  candidates    ->  data/digests.jsonl                      (one subject Digest per day)
pick       offline   candidates    ->  data/picks.jsonl                        (single-image fallback; manual only)
publish    offline*  digests,picks ->  site/_posts/<date>-<subject|source>.md + site/assets/img/<date>/
debug-pages offline  candidates    ->  site/debug/<source>.html                (explorer pages)
```

`*` digest may download two previews to build a wigglegram; publish downloads each panel's display image if it isn't cached.

Each stage reads and writes files, so any stage can be developed against what's already on disk.
`spacepics pipeline` runs fetch, extract, download (render-on-view sources only), digest, publish, debug-pages in
order; that's what the daily job calls. `pick` is a separate command the daily job does not run.

fetch and extract isolate failures per source: one broken feed is logged and skipped, the rest continue, and the
picker works with whatever sources have fresh candidates. A source that fails every day just stops contributing.

`store.read_candidates(source, days=N)` concatenates the newest N daily files, de-duplicated by key with the newest
winning. The picker reads one day; the ranker's rolling window will ask for more.

The image cache (`data/images/`, gitignored, flat files keyed by URL hash) can be pointed elsewhere with
`SPACEPICS_IMAGES_DIR` so several worktrees share one cache instead of re-downloading.

## The contract between sources and everything else

A source implements `Source` (`sources/base.py`):

- `fetch_feed(client) -> bytes`: network only, returns the raw response to be saved as-is.
- `extract(raw: bytes) -> list[Candidate]`: pure function of the bytes. Testable from a fixture.

Sources keep their own pydantic models for the feed shape (see `perseverance.py`: `RawFeed`, `RawImage`).
Those never leave the source module. `Candidate` (`models.py`) is the only thing later stages see:

| Field | Meaning |
|---|---|
| `source`, `source_id` | adapter name and a stable id within it; `key` is `source:source_id` |
| `instrument` | grouping key for per-instrument ranking and debug galleries |
| `captured_at` | UTC, tz-aware |
| `image_url` | display size, roughly 1000 to 2000 px |
| `preview_url` | smaller image for embedding; may equal `image_url` |
| `title`, `credit`, `source_page_url` | for the post |
| `meta` | anything source-specific a later stage might want (filter name, sol, RA/Dec, wavelength) |

If a later stage needs a new cross-source field, add it to `Candidate` with a default so existing sources keep working.

## The daily post: subject-of-the-day digest

`digest.build_digest(sources, day)` picks a subject by rotating Sun, Mars, Earth on the calendar day (skipping any
subject with nothing fresh), runs that subject's recipe (`digest.RECIPES`) over the fresh pools to choose up to six
panels, and records a `Digest` in `data/digests.jsonl`. Recipes are simple and seeded: Mars takes the latest sol's
colour Mastcam-Z frames, a navcam, a close-up instrument, Curiosity, and HiRISE; Sun takes four SDO channels nearest
noon and a few Helioviewer companions; Earth takes three GOES frames across the day and two EPIC frames.

`publish` writes one post per digest (`site/_posts/<date>-<subject>.md`), copies each panel's display image into
`site/assets/img/<date>/`, and renders each panel with its instrument card and readable metadata. The single-image
`pick` still exists as a CLI command and a fallback; the daily job runs the digest.

## Instrument cards

`data/reference/instruments/*.yaml` (schema in `data/reference/README.md`) holds one hand-maintained card per
spacecraft and instrument, matched on the exact `spacecraft` and `instrument` values candidates carry.
`reference.card_for` finds the card; `reference.readable_meta` turns `Candidate.meta` into labelled lines using
common labels plus the card's own. Cards are the learning layer: what the instrument is, what it sees, how to read
the frame, Wikipedia links. Adding a source means adding a card.

## Picking (single image; fallback)

`pipeline.pick(sources, day, chooser)` builds pools of fresh candidates per source (each source declares its own
`freshness_days`), hands them to a chooser along with previous picks, and persists the result. Choosers only decide.

A chooser returns a `Choice`: the candidate, a caption, a `picker` label (recorded on the Pick so old picks stay
explained), and optionally a `derived_image` (a path under `data/`, e.g. a multispectral composite) with the
candidate keys it was built from. When `derived_image` is set the publisher copies that file into `site/` instead
of downloading the candidate's image; the candidate is then the anchor frame.

`choose_random` is the placeholder: weighted source (each source declares `weight`), uniform instrument within the
source, uniform frame, skipping yesterday's source when possible. The planned replacement: per-instrument embedding
anomaly score over a rolling window, top-N to a vision model that picks one and writes the caption. That is another
chooser; nothing else changes.

## Explorer pages (site/debug/)

Plain HTML per source, opened from disk or served by Pages, linking to remote images (lazy-loaded). Layout is chosen
per source in `publish.gallery_context`: rovers get sol -> sequence -> frames (a sequence is one observation, e.g. a
filter set side by side); SDO gets a channel-by-time grid; everything else groups by instrument. Pages fold in the
last 30 days of committed candidates plus anything under `data/survey/<source>/` (committed exploration fetches of
other dates, run through the same extractor). Render-on-view sources (`publish.RENDER_ON_VIEW`, currently
`helioviewer`) never link the live render URL; cached previews are copied under `site/debug/img/<source>/` instead.

## Site and deploy

Jekyll with `jekyll-feed` (Atom feed at `/feed.xml`) and no theme. One post per pick; the post body embeds
the image with `absolute_url` so feed readers see it. `site/debug/` is plain HTML copied through untouched.

`.github/workflows/daily.yml` is a single workflow: pipeline job (runs `spacepics pipeline`, commits `data/`
and `site/`), then Jekyll build, then Pages deploy. It's one workflow because commits made with the default
Actions token don't trigger other workflows. Pushes to `main` that touch `site/` or `src/` skip the pipeline
job and just rebuild and deploy.
