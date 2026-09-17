# Tasks

Claim before starting: put your name or session in Owner and list the files you expect to touch.
Keep claims small and disjoint. Mark done with the commit hash. Newest at the top of each list.

## In progress

| Task | Owner | Files | Notes |
|---|---|---|---|
| Source: SDO extract | subagent (Claude, main tree) | `sources/sdo.py`, `tests/test_sdo.py`, `tests/fixtures/sdo_*` | Feed + images already fetched by Keith's session; no network. |
| Source: ESA Webb/Hubble extract | subagent (Claude, main tree) | `sources/esa.py`, `tests/test_esa.py`, `tests/fixtures/esa_*` | Same. |
| Source: EPIC extract | subagent (Claude, main tree) | `sources/epic.py`, `tests/test_epic.py`, `tests/fixtures/epic_*` | Same. |
| Source: APOD + HiRISE extract | subagent (Claude, main tree) | `sources/apod.py`, `sources/hirise.py`, `tests/test_apod.py`, `tests/test_hirise.py`, fixtures | Same. |

## Ready

| Task | Files | Notes |
|---|---|---|
| Per-source freshness window | `sources/base.py`, `pipeline.py` | Monthly/weekly sources (ESA) need more than 7 days. |
| Compress saved feeds | `pipeline.py` | SDO's listing is 1.2 MB/day uncompressed; decide gzip-on-save before the repo grows. |
| Perseverance paging | `sources/perseverance.py` | Pull pages 0..N so a full sol is covered. |
| Ranker: per-instrument embedding anomaly | `rank.py`, `pipeline.py`, `pyproject.toml` | DINOv2-small on CPU; rolling window persisted under `data/embeddings/`. |
| Picker: vision model pick + caption | `pick.py`, `pipeline.py` | Decision on provider pending. |
| Index page: last N picks as a grid | `site/index.md`, `site/assets/css/style.css` | |

## Done

| Task | Commit |
|---|---|
| Skeleton: models, Perseverance source, stages, CLI, Jekyll site, workflows, docs | |
