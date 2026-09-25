# White balance for Mastcam-Z colour frames (shelved 2026-09-25)

KT-282 quest 3. Shelved by Keith: "interesting but not useful for this particular sample of pictures". Come back to it
on a day with more colour imaging.

## Where the code is
Branch `experiment/white-balance` (not merged):
- `src/spacepics/colour.py` has three variants: robust grey-world (the default), plain grey-world, and white-patch.
  The robust version masks out borders, saturated pixels and sky, uses a trimmed mean, and caps the gain.
- `tests/test_colour.py`
- `experiments/white_balance_grid.py` rebuilds a before/after grid from whatever is in the image cache. Run it with
  `uv run --env-file .env experiments/white_balance_grid.py`.
- `docs/research/white-balance/` holds the 2026-09-25 grid (12 rows) and the full review notes.

To resume, run `git switch experiment/white-balance`, or rebase it onto main first.

## What we learned
- **Most "colour" Mastcam-Z previews are greyscale.** 46 of the 56 cached `ZCAM_*0_RGB` previews (sols 1981-1990)
  had R = G = B. The only true colour frames were the calibration-target sequence ZCAM03029. With nothing to balance,
  the experiment had little to act on.
- **Grey-world is the wrong prior for Mars.** It assumes the average of a scene is grey, but Mars really is reddish.
  On navcam, hazcam and dust crops it turns the scene into a grey moonscape, with a blue gain around 1.4.
- **White-patch looked closest to right** on the calibration target (blue gain about 1.07-1.10, compared with 1.23
  for grey-world). A proper calibration would use the target's known patches, and picture-type labels (KT-282 quest 6)
  could find those frames automatically.

## If we pick it up again
- First check that the day has real colour frames. The digest's real-colour check (KT-282 follow-up) makes this easy.
- Try white-patch or a half-strength correction rather than full grey-world. Keith's taste is "looks right", not
  calibrated.
- Decide whether it replaces the raw colour panel or adds a panel. The agent leaned towards replacing it.
