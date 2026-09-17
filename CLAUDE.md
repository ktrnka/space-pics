# CLAUDE.md — space-pics

Daily space image picker. Pulls recent imagery from public space feeds, picks one, publishes a static site with RSS.
Jekyll site in `site/`, deployed to GitHub Pages by the daily Actions job. No server, no database.

Read `docs/ARCHITECTURE.md` before touching the pipeline, `docs/SOURCES.md` before touching a source,
and `docs/TASKS.md` before starting work (claim a task there so parallel sessions don't collide).

## Quick start

```bash
uv sync
uv run spacepics --help
uv run spacepics pipeline          # fetch -> extract -> download(helioviewer) -> digest -> publish -> debug-pages
uv run spacepics digest --day 2026-09-17   # rebuild one day's subject digest offline
uv run pytest -q && uv run ruff check src tests
cd site && bundle install && bundle exec jekyll serve   # http://localhost:4000/space-pics/
```

Debug galleries need no Jekyll: `uv run spacepics debug-pages` then open `site/debug/index.html` in a browser.

## What lives where

| What | Where |
|---|---|
| Source adapters (one file per source) | `src/spacepics/sources/` |
| Cross-source models (`Candidate`, `Pick`) | `src/spacepics/models.py` |
| Pipeline stages | `src/spacepics/pipeline.py`, `src/spacepics/publish.py` |
| Raw feed responses (committed) | `data/feeds/<source>/<date>.json` |
| Extracted candidates (committed) | `data/candidates/<source>/<date>.jsonl` |
| Downloaded images (gitignored cache) | `data/images/<source>/` |
| Daily digests and picks | `data/digests.jsonl`, `data/picks.jsonl` |
| Instrument cards (hand-maintained) | `data/reference/instruments/*.yaml` |
| Date-survey feeds (committed, exploration) | `data/survey/<source>/` |
| Jekyll site, generated posts, chosen images | `site/`, `site/_posts/`, `site/assets/img/<date>/` |
| Test fixtures (trimmed real feed responses) | `tests/fixtures/` |

## Conventions

- Network and processing are separate stages. `fetch` and `download` touch the network; `extract`, `pick`, `publish` work from disk. Iterate on parsing and picking without re-hitting the sites.
- Each source keeps its own raw pydantic models for the feed shape. Only `Candidate` crosses into the rest of the pipeline; source-specific extras go in `Candidate.meta`.
- Never download FITS, JPEG2000, or full-resolution products. Use each source's JPEG/PNG previews.
- Tests are slim: one fixture plus a parse test per source. Save a trimmed real response as the fixture, not a hand-written one.
- Data (`data/`, `site/`) and code (`src/`, `tests/`) stay in separate directories.
- `uv run` for everything Python. Ruff at line length 150.
- Small commits with clear messages; the git log is part of the project timeline. Log notable timestamps and scope changes in `NOTES.md`.

## Parallel work

Use a git worktree per task so sessions don't share a working tree:

```bash
git worktree add ../space-pics-<task> -b <task>
cd ../space-pics-<task> && uv sync
export SPACEPICS_IMAGES_DIR=/home/keith/code/space-pics/data/images   # share the main tree's image cache; never re-download
```

Subagents and parallel sessions work offline: the main session fetches feeds and images once, everything else
runs from `data/`. Per-source knobs (`enabled`, `freshness_days`, `weight`) live on the adapter class.

Claim the task in `docs/TASKS.md` with the files you expect to touch. Adding a source touches only
`src/spacepics/sources/<name>.py`, its registration line in `sources/__init__.py`, one fixture, one test file,
and a section in `docs/SOURCES.md`.
