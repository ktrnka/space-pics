# Tasks

Claim before starting: put your name or session in Owner and list the files you expect to touch.
Keep claims small and disjoint. Mark done with the commit hash. Newest at the top of each list.

## In progress

| Task | Owner | Files | Notes |
|---|---|---|---|

## Ready

| Task | Files | Notes |
|---|---|---|
| Source: SDO latest images | `sources/sdo.py`, `sources/__init__.py`, `tests/test_sdo.py`, `tests/fixtures/sdo_*`, `docs/SOURCES.md` | See SOURCES.md for the URL pattern. Fetch can save a manifest JSON rather than a feed. |
| Source: ESA Hubble/Webb picture of the month | `sources/esa.py`, same pattern | Put RA/Dec/FOV in `meta`. |
| Source: NASA EPIC | `sources/epic.py`, same pattern | Needs `NASA_API_KEY` from env. |
| Perseverance paging | `sources/perseverance.py` | Pull pages 0..N so a full sol is covered. |
| Ranker: per-instrument embedding anomaly | `rank.py`, `pipeline.py`, `pyproject.toml` | DINOv2-small on CPU; rolling window persisted under `data/embeddings/`. |
| Picker: vision model pick + caption | `pick.py`, `pipeline.py` | Decision on provider pending. |
| Index page: last N picks as a grid | `site/index.md`, `site/assets/css/style.css` | |

## Done

| Task | Commit |
|---|---|
| Skeleton: models, Perseverance source, stages, CLI, Jekyll site, workflows, docs | |
