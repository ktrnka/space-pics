# Notes (build-day timeline)

2026-09-17. Times are Pacific.

- 08:00 window opens; research and scoping (see `vibe-day-handoff.md`, `space-image-of-the-day-research.md`)
- 10:00 research end; Perseverance feed and SDO URLs verified with curl
- 10:05 decisions: Python 3.14, uv, Jekyll in `site/`, single combined daily workflow, state committed to repo, PoC = one source + random pick
- 10:25 first thing that ran: `spacepics pipeline` end to end on Perseverance (100 candidates, random pick, post written)
- 10:26 local Jekyll build with Atom feed
- 10:33 first thing worth showing someone: site, feed, and debug gallery live at https://ktrnka.github.io/space-pics/ (Keith created the repo and ran the workflow; job took 1m07s)
- stall: Mars feed 302'd to HTML because `order=sol+desc` had its `+` percent-encoded (about 5 min)

- 10:47 feeds fetched once for sdo, esa_webb, esa_hubble, epic, apod, hirise; 100 images (23 MB) cached locally so extractor work can be delegated offline

## Scope changes from the must-do note

- (none yet)
