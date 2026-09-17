"""Wigglegram: a stereo pair (left/right eye, same instant) alternated as a two-frame GIF to fake depth.

Frames are aligned on the centre of the scene (the subject). The near/far parallax spread decides whether a pair is
worth showing (too little: no depth; too much: a ground plane sliding sideways) and how slowly to alternate.
Everything here is best effort: callers should treat None as "no wigglegram today".
"""

import logging
import re
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image

from .models import Candidate
from .paths import DATA_DIR
from .pipeline import download_url, make_client

logger = logging.getLogger(__name__)

WIDTH = 640
MIN_SPREAD, MAX_SPREAD = 8, 40  # px at WIDTH
EYE_RE = re.compile(r"^[A-Z][LR][A-Z0-9]_")  # NLF/NRF, ZL0/ZR0 prefixes


def _best_shift(ga, gb, ys, xs, dy_range=range(-6, 7, 2), dx_range=range(-90, 91, 2)) -> tuple[int, int]:
    h, w = ga.shape
    ref = ga[ys, xs]
    ref = ref - ref.mean()
    best, best_dx, best_dy = -1e18, 0, 0
    for dy in dy_range:
        for dx in dx_range:
            y0, y1, x0, x1 = ys.start - dy, ys.stop - dy, xs.start - dx, xs.stop - dx
            if y0 < 0 or x0 < 0 or y1 > h or x1 > w:
                continue
            pb = gb[y0:y1, x0:x1]
            pb = pb - pb.mean()
            score = (ref * pb).sum() / (np.sqrt((ref * ref).sum() * (pb * pb).sum()) + 1e-6)
            if score > best:
                best, best_dx, best_dy = score, dx, dy
    return best_dx, best_dy


def align(a: Image.Image, b: Image.Image) -> tuple[int, int, int]:
    """(dx, dy, spread): shift aligning b onto a at the centre, and the near/far parallax spread in px."""
    ga = np.asarray(a.convert("L"), dtype=np.float32)
    gb = np.asarray(b.convert("L"), dtype=np.float32)
    h, w = ga.shape
    xs = slice(w // 4, 3 * w // 4)
    dx, dy = _best_shift(ga, gb, slice(h // 3, 2 * h // 3), xs)
    dx_far, _ = _best_shift(ga, gb, slice(h // 8, 3 * h // 8), xs, dy_range=[dy])
    dx_near, _ = _best_shift(ga, gb, slice(5 * h // 8, 7 * h // 8), xs, dy_range=[dy])
    return dx, dy, abs(dx_far - dx_near)


def duration_ms(spread_px: int) -> int:
    return int(min(600, 220 + 8 * spread_px))


def mastcam_pairs(candidates: list[Candidate]) -> list[tuple[Candidate, Candidate]]:
    """Left/right colour Mastcam-Z frames of the same sequence, paired by order (the eyes expose minutes apart)."""
    seqs: dict[tuple, dict[str, list[Candidate]]] = {}
    for c in candidates:
        if c.instrument in ("MCZ_LEFT", "MCZ_RIGHT") and (c.meta.get("filter_name") or "").endswith("RGB") and c.meta.get("sequence"):
            seqs.setdefault((c.meta.get("sol"), c.meta["sequence"]), {"L": [], "R": []})[c.instrument[4]].append(c)
    pairs = []
    for (_sol, _seq), d in sorted(seqs.items(), reverse=True):
        for left, right in zip(sorted(d["L"], key=lambda c: c.captured_at), sorted(d["R"], key=lambda c: c.captured_at), strict=False):
            pairs.append((left, right))
    return pairs


def build(left: Candidate, right: Candidate, day: date) -> tuple[str, int, int] | None:
    """Make the GIF under data/derived/. Returns (path relative to data/, spread, duration) or None if the pair doesn't qualify."""
    with make_client() as client:
        a = Image.open(download_url(client, str(left.preview_url))).convert("RGB")
        b = Image.open(download_url(client, str(right.preview_url))).convert("RGB")
    a = a.resize((WIDTH, int(a.height * WIDTH / a.width)))
    b = b.resize(a.size)
    dx, dy, spread = align(a, b)
    if not MIN_SPREAD <= spread <= MAX_SPREAD:
        logger.info("wigglegram: %s spread %d px, outside %d..%d", left.key, spread, MIN_SPREAD, MAX_SPREAD)
        return None
    shifted = Image.new("RGB", a.size, "black")
    shifted.paste(b, (dx, dy))
    crop = (abs(dx), abs(dy), a.width - abs(dx), a.height - abs(dy))
    frames = [a.crop(crop), shifted.crop(crop)]
    rel = Path("derived") / day.isoformat() / f"wiggle-{left.source}-{left.meta.get('sol')}-{left.meta.get('sequence')}.gif"
    out = DATA_DIR / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    ms = duration_ms(spread)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)
    return str(rel), spread, ms


def best_wigglegram(candidates: list[Candidate], day: date, max_tries: int = 4) -> tuple[Candidate, Candidate, str, int, int] | None:
    """First qualifying Mastcam-Z colour pair among the newest sequences. Any failure means None."""
    for left, right in mastcam_pairs(candidates)[:max_tries]:
        try:
            result = build(left, right, day)
        except Exception:
            logger.exception("wigglegram failed for %s", left.key)
            continue
        if result:
            rel, spread, ms = result
            return left, right, rel, spread, ms
    return None
