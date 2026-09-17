# Vibe day handoff — space image of the day

Read this first. Companion doc: `space-image-of-the-day-research.md` (sources, endpoints, sizes, libraries).

## What today is

A one-day, time-boxed build. Keith is running an experiment: greenfield app, strict 8-hour window, code freeze at 4pm, "shipped" judged at 4. The goal is a fun day and a thing he'll check daily — not a perfect codebase. Optimise for a working, deployed site by 4pm over architecture.

**Date:** 2026-09-17. **Window:** 8:00–17:00 with a 12–1 lunch. **Code freeze: 16:00.** After freeze: testing, sending to a friend, debrief. No new code after 4.

## Must-do (the bar for "done")

A static site showing **one recent image per day**, picked automatically from **at least two sources** (Mars raw feed + one other), with a **caption** and an **RSS feed**, rebuilt by a **daily GitHub Actions job**.

Friend-usable means: they open the URL, or subscribe to the RSS. Hosted = GitHub Pages or similar; no server.

## Cut order (cut from the left first if behind)

sky-map inset → anomaly ranker (fall back to VLM-only pick) → multispectral composite → Rubin transient source → third source

If the Rubin broker query is still fighting at ~10:30, cut it without discussion.

## Build order that keeps the demo alive

1. Source adapters (Mars raw feed, SDO latest) returning `[{url, instrument, timestamp, meta}]` — verify with curl before writing the adapter.
2. Download previews → embed → per-instrument anomaly score (rolling window; backfill ~7 days on first run).
3. VLM picks one from the top-N and writes the caption.
4. Static site + RSS generation. Deploy. **Get a URL live early**, even with a hardcoded image — the deploy path is not something to discover at 3:30.
5. Then stretch items in reverse cut order.

## Working style for this day

- Keith's normal process: he holds decisions on **stack, data model, and hosting**. Ask before choosing between meaningfully different options there; don't ask about things a lint hook would settle.
- Prefer boring, known tools (Python, plain HTML/CSS, GitHub Actions, GitHub Pages). No frameworks that need a learning curve today.
- Use each source's JPEG/PNG previews. Never download FITS or full-resolution products today.
- Keep the daily build cheap: a few hundred small JPEGs, CPU embeddings. Measure Actions job time on the first real run.
- Small commits with clear messages — the git log is part of the debrief timeline.
- Be explicit about which facts came from the research doc's **(from memory)** entries; confirm with a request before building on them.

## Timestamps to capture for the debrief

Note (in a `NOTES.md` or commit messages) the times of: research end, first thing that ran, first thing worth showing someone, code freeze, and the biggest single stall. Also log any point where scope moved from the must-do note and why (decision vs drift).

## Things that are out of scope today

- Reading/processing FITS or JPEG2000 full products (HiRISE full-res, JWST `_i2d`, Helioviewer JP2)
- LROC, BepiColombo (science camera not on until orbit insertion in Nov 2026), JunoCam
- A trained classifier; anything needing labels
- User accounts, a backend, a database
- Polish beyond "looks fine on phone and desktop"

## Guardrails (from the vibe-day setup)

- Greenfield only; no reuse of termcap code.
- Pre-provisioned generic infra is fine (repo, Pages, an api.nasa.gov key). App-specific work is not pre-done.
- Disposable by default: no maintenance commitment.
- If it isn't done at 4, it isn't done. Finishing early means testing and polish, not a second feature list.
