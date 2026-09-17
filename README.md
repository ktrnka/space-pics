# space-pics

One recent image from space, every day, picked automatically from public raw feeds and published as a static site with RSS.

Site: https://ktrnka.github.io/space-pics/ · Feed: https://ktrnka.github.io/space-pics/feed.xml

## How it works

A daily GitHub Actions job runs `spacepics pipeline`: fetch the sources' feeds, extract candidate images, build a
subject-of-the-day digest (Sun, Mars, or Earth, rotating daily) of a few panels with instrument cards, write a Jekyll
post, commit, and deploy to GitHub Pages. A single-image `pick` command still exists as a manual fallback but isn't
part of the daily job. Explorer pages under `/debug/` show every candidate per source, grouped by instrument.

## Develop

```bash
uv sync
uv run spacepics pipeline
uv run spacepics digest --day 2026-09-17   # rebuild one day's subject digest offline; see docs/ARCHITECTURE.md
uv run pytest -q
cd site && bundle install && bundle exec jekyll serve
```

See `CLAUDE.md` for conventions and `docs/` for architecture, sources, and the task board.

Built in a one-day time-boxed session on 2026-09-17. Images belong to their sources; each post carries a credit.
