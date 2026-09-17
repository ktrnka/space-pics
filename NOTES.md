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
- 11:30 cleanup pass: per-source failure isolation, chooser seam (with derived-image support for composites), rolling-window store, weights on sources
- 11:05 four subagents (sdo, esa, epic, apod+hirise) wrote extractors offline in parallel, same working tree, disjoint file sets; 3 to 7 minutes each; all seven sources extract (219 candidates)
- 12:00-12:50 (Keith at lunch): research subagent surveyed 13 feeds with one verification request each; Helioviewer
  adapter (29 layers, one API for SOHO/STEREO/GOES/PROBA-2/Hinode/Solar Orbiter/PUNCH) with the embargo pattern visible
  in the manifest; Curiosity, GOES-19 GeoColor, NOIRLab sources; explorer pages with sequence and time-grid layouts;
  week-long date survey (about 620 requests, paced, 45 MB); embedding experiment (DINOv2 27 img/s on CPU; global
  embeddings flat on the Sun, frame differences find a flare); Candidate gained spacecraft, released_at, thumbnail_url
- 13:05 Keith's review of the explorer and anomaly page; reset around four criteria (public, RSS not regrettable,
  shareable, personal excitement); plan: instrument cards + digest + CI verify
- 13:50 first subject-of-the-day digests published (Mars today; Sun and Earth as backdated demos from today's data)
- 13:55 first unattended-style CI run of the full pipeline succeeded end to end (fetch, extract, download, digest,
  publish, bot commit, Jekyll build, Pages deploy); the earlier attempt failed only on a push race with my own pushes
- 14:00 all 47 instrument keys have a verified or from-memory card (3 subagents, ~6 to 9 minutes each)
- 14:20 Keith's review of the live Mars page: captions to one line with tooltips, explorer links per panel, colloquial headings
- 14:30 stall: push-triggered runs had never deployed since 10:40 (deploy job silently skipped because the pipeline job
  upstream was skipped on push; only the bot's own runs deployed). Found via last-modified headers. One-line fix.
  Also: Helioviewer digest images were saved with the render URL's query string as the extension (404 on Pages).
- 14:55 all three subject pages reviewed live by Keith and revised: captions, headings, Sun ordering, Earth slimmed
- 15:09 wigglegram proof of concept (three Perseverance stereo pairs) as an experiment page
- 15:11 final CI run dispatched; **code freeze 16:00** (no code after the final run's bot commit)
- biggest single stall of the day: push-triggered deploys silently skipped for four hours (found 14:30, one-line fix)

## Scope changes from the must-do note

- 12:00 **decision**: must-do met (multi-source, auto pick, caption, RSS, daily job, live URL). Keith's gallery review
  concluded we jumped from data to the pick-1 demo too early. Afternoon scope replaces the stretch list with:
  (1) expand sources per subject (Sun, Mars, Earth first) so subject-of-the-day is viable; (2) survey more dates for
  existing sources to look for stories; (3) explorer pages grouped by subject with a time axis; (4) embargo-aware
  sources (release tier, released_at) with reference lookups by time or sky position. The pick-1 job keeps running as
  the fallback that keeps the site alive.
