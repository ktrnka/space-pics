# Architecture

## Stages

```
fetch      network   source feeds  ->  data/feeds/<source>/<date>.json      (saved verbatim)
extract    offline   saved feed    ->  data/candidates/<source>/<date>.jsonl (list of Candidate)
download   network   candidates    ->  data/images/<source>/<id>.preview.jpg (gitignored cache)
pick       offline   candidates    ->  data/picks.jsonl                      (one Pick per day)
publish    offline*  picks         ->  site/_posts/<date>-<source>.md + site/assets/img/<date>/
debug-pages offline  candidates    ->  site/debug/<source>.html              (per-instrument galleries)
```

`*` publish downloads the one display-size image for the pick if it isn't cached.

Each stage reads and writes files, so any stage can be developed against what's already on disk.
`spacepics pipeline` runs fetch, extract, pick, publish, debug-pages in order; that's what the daily job calls.

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

## Picking

`pick_random` is a placeholder: a seeded random choice among candidates captured in the last 7 days.
The planned replacement is: per-instrument embedding anomaly score over a rolling window, top-N to a
vision model that picks one and writes the caption. The pick stage records `picker` so old picks stay explained.

## Site and deploy

Jekyll with `jekyll-feed` (Atom feed at `/feed.xml`) and no theme. One post per pick; the post body embeds
the image with `absolute_url` so feed readers see it. `site/debug/` is plain HTML copied through untouched.

`.github/workflows/daily.yml` is a single workflow: pipeline job (runs `spacepics pipeline`, commits `data/`
and `site/`), then Jekyll build, then Pages deploy. It's one workflow because commits made with the default
Actions token don't trigger other workflows. Pushes to `main` that touch `site/` or `src/` skip the pipeline
job and just rebuild and deploy.
