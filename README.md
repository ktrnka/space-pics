# space-pics

One recent image from space, every day, picked automatically from public raw feeds and published as a static site with RSS.

Site: https://ktrnka.github.io/space-pics/ · Feed: https://ktrnka.github.io/space-pics/feed.xml

## How it works

A daily GitHub Actions job runs `spacepics pipeline`: fetch the sources' feeds, extract candidate images,
pick one, write a Jekyll post with the image, commit, and deploy to GitHub Pages. The pick is currently a
seeded random choice; ranking and a vision-model caption come next.

## Develop

```bash
uv sync
uv run spacepics pipeline
uv run pytest -q
cd site && bundle install && bundle exec jekyll serve
```

See `CLAUDE.md` for conventions and `docs/` for architecture, sources, and the task board.

Built in a one-day time-boxed session on 2026-09-17. Images belong to their sources; each post carries a credit.
