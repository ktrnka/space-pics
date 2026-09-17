# Ideas

A parking lot for things noticed while looking at the output. Not commitments. When one is worth exploring,
move it to `docs/TASKS.md` with a file set so an agent can take it in a worktree.

Format: one bullet per idea, with enough context that someone who didn't see the trigger can evaluate it.
Add a date and where the idea came from (which debug page, which pick).

## Image processing

- **Colour-correct Mastcam-Z frames against the calibration target** (2026-09-17, from the perseverance debug page).
  The raw-feed browse JPEGs are not calibrated; official "natural colour" and "white-balanced" releases are
  produced by the instrument team using the deck calibration target (grey rings, colour swatches, shadow post).
  Question to explore: can we find caltarget frames in the feed (fixed pointing, so mast az/el in the feed's
  `extended` block should identify them), estimate per-channel gains from the known swatch reflectances, and apply
  them to same-sol frames? Limits: 8-bit JPEG browse products with unknown onboard processing, so "looks right",
  not science-grade.

## Sources

- Perseverance paging beyond the first 100 frames so a whole sol is covered.

## Site

- Per-instrument debug galleries for every source, linked from a debug index (exists for perseverance; keep it as sources are added).
- User interface theme inspired from classic space UIs, or actually maybe Mass Effect? It'd be pretty dope to have a ME theme