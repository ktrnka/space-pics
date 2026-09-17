# Notes (build-day timeline)

2026-09-17. Times are Pacific.

- 08:00 window opens; research and scoping (see `vibe-day-handoff.md`, `space-image-of-the-day-research.md`)
- 10:00 research end; Perseverance feed and SDO URLs verified with curl
- 10:05 decisions: Python 3.14, uv, Jekyll in `site/`, single combined daily workflow, state committed to repo, PoC = one source + random pick
- 10:25 first thing that ran: `spacepics pipeline` end to end on Perseverance (100 candidates, random pick, post written)
- 10:26 local Jekyll build with Atom feed
- stall: Mars feed 302'd to HTML because `order=sol+desc` had its `+` percent-encoded (about 5 min)

## Scope changes from the must-do note

- (none yet)
