# Tasks

Claim before starting: put your name or session in Owner and list the files you expect to touch.
Keep claims small and disjoint. Mark done with the commit hash. Newest at the top of each list.

## In progress

| Task | Owner | Files | Notes |
|---|---|---|---|

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
| Skeleton: models, Perseverance source, stages, CLI, Jekyll site, workflows, docs | 27bb139..5b4f945 |
| Sources sdo, esa_webb, esa_hubble, epic, apod, hirise: fetch halves by main session, extractors by 4 parallel subagents | (this commit) |
| Per-source freshness window | (this commit) |
