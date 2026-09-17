"""Subject-of-the-day digest: one post per day about one subject, a few panels from that subject's sources.

Subjects rotate by calendar day (Sun, Mars, Earth), skipping any subject with nothing fresh. Panel recipes are
per subject and deliberately simple; the "what's interesting" signals replace the seeded random choices later.
"""

import logging
import random
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from .models import Candidate
from .paths import DATA_DIR
from .pipeline import fresh, image_ext, safe_name
from .reference import card_for, panel_heading
from .sources import Source
from .store import read_candidates

logger = logging.getLogger(__name__)

DIGESTS_FILE = DATA_DIR / "digests.jsonl"
ROTATION = ["Sun", "Mars", "Earth"]
MAX_PANELS = 6


class Panel(BaseModel):
    candidate: Candidate
    site_image: str  # relative to site/
    heading: str  # e.g. "Mastcam-Z, left eye"
    blurb: str  # one or two sentences from the instrument card
    derived_image: str | None = None  # relative to data/: a locally built image (e.g. a wigglegram) shown instead of the candidate's
    derived_from: list[str] = []


class Digest(BaseModel):
    day: date
    subject: str
    title: str
    intro: str
    panels: list[Panel]


def read_digests() -> list[Digest]:
    if not DIGESTS_FILE.exists():
        return []
    return [Digest.model_validate_json(line) for line in DIGESTS_FILE.read_text().splitlines() if line.strip()]


def upsert_digest(d: Digest) -> None:
    items = [x for x in read_digests() if x.day != d.day] + [d]
    items.sort(key=lambda x: x.day)
    DIGESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DIGESTS_FILE.write_text("".join(x.model_dump_json() + "\n" for x in items))


def choose_subject(day: date, available: set[str]) -> str:
    start = day.toordinal() % len(ROTATION)
    for i in range(len(ROTATION)):
        subject = ROTATION[(start + i) % len(ROTATION)]
        if subject in available:
            return subject
    raise RuntimeError("no subject has fresh candidates")


def _pick(rng: random.Random, pool: list[Candidate], n: int = 1) -> list[Candidate]:
    pool = sorted(pool, key=lambda c: c.key)
    return rng.sample(pool, min(n, len(pool)))


def _by(pool: list[Candidate], **conds) -> list[Candidate]:
    out = []
    for c in pool:
        ok = True
        for k, v in conds.items():
            val = c.meta.get(k) if k in c.meta else getattr(c, k, None)
            ok &= (val in v) if isinstance(v, (list, set, tuple)) else (val == v)
        if ok:
            out.append(c)
    return out


def recipe_mars(rng: random.Random, pools: dict[str, list[Candidate]]) -> list[Candidate]:
    p = pools.get("perseverance", [])
    latest_sol = max((c.meta.get("sol", 0) for c in p), default=None)
    sol = [c for c in p if c.meta.get("sol") == latest_sol]
    picks = []
    picks += _pick(rng, _by(sol, instrument=["MCZ_LEFT", "MCZ_RIGHT"], filter_name=["ZCAM_L0_RGB", "ZCAM_R0_RGB"]), 2)
    picks += _pick(rng, _by(sol, instrument=["NAVCAM_LEFT", "NAVCAM_RIGHT"]), 1)
    picks += _pick(rng, _by(sol, instrument=["SUPERCAM_RMI", "SHERLOC_WATSON"]), 1)
    picks += _pick(rng, pools.get("curiosity", []), 1)
    picks += _pick(rng, pools.get("hirise", []), 1)
    if len(picks) < 3:  # thin sol: fall back to anything fresh from the rover
        picks += _pick(rng, [c for c in p if c not in picks], 3 - len(picks))
    return picks


def recipe_sun(rng: random.Random, pools: dict[str, list[Candidate]]) -> list[Candidate]:
    sdo = pools.get("sdo", [])
    hv = pools.get("helioviewer", [])

    def noon(frames):
        return min(frames, key=lambda c: abs(c.captured_at.hour - 12)) if frames else None

    # Surface outward: HMI continuum, AIA 304 (chromosphere), AIA 193 beside SUVI 195 (same iron ion, two spacecraft),
    # the AIA composite, then the coronagraph.
    suvi = [c for c in _by(hv, instrument="GOES SUVI") if str(c.meta.get("measurement")) == "195"] or _by(hv, instrument="GOES SUVI")
    ordered = [noon(_by(sdo, instrument="HMIIC")), noon(_by(sdo, instrument="0304")), noon(_by(sdo, instrument="0193"))]
    ordered += _pick(rng, suvi, 1)
    ordered += [noon(_by(sdo, instrument="211193171"))]
    ordered += _pick(rng, _by(hv, instrument="SOHO LASCO C2"), 1)
    return [c for c in ordered if c is not None]


def recipe_earth(rng: random.Random, pools: dict[str, list[Candidate]]) -> list[Candidate]:
    picks = []
    goes = pools.get("goes", [])
    if goes:  # the 00 UTC frame: dusk on the US west coast, night in the east; the most legible GeoColor of the day
        newest_day = max(c.captured_at.date() for c in goes)
        day_frames = [c for c in goes if c.captured_at.date() == newest_day]
        picks.append(min(day_frames, key=lambda c: c.captured_at.hour))
    picks += _pick(rng, pools.get("epic", []), 2)
    return picks


RECIPES = {"Mars": recipe_mars, "Sun": recipe_sun, "Earth": recipe_earth}
TITLES = {"Mars": "Mars, {day}", "Sun": "The Sun, {day}", "Earth": "Earth, {day}"}
INTROS = {
    "Mars": "{n} recent images of Mars from {craft}. Capture times are in the captions; a sol is a Mars day.",
    "Sun": "{n} views of the Sun from {craft}, ordered from the surface outward: the visible surface, then the hot corona in "
    "ultraviolet from two different spacecraft, then the outer corona seen by a coronagraph that blocks the disc.",
    "Earth": "{n} recent images of Earth from {craft}: the sunlit disc from geostationary orbit, and the whole planet from a million miles away.",
}


def build_digest(sources: list[Source], day: date) -> Digest:
    pools = {s.name: fresh(read_candidates(s.name), day, s.freshness_days) for s in sources}
    subjects = {s.subject for s in sources if pools[s.name]}
    subject = choose_subject(day, subjects & set(ROTATION))
    rng = random.Random(f"{day.isoformat()}:{subject}")
    picks = RECIPES[subject](rng, {s.name: pools[s.name] for s in sources if s.subject == subject})[:MAX_PANELS]
    if not picks:
        raise RuntimeError(f"recipe for {subject} produced no panels")
    panels = [_panel(c, day) for c in picks]
    if subject == "Mars":
        panels += _wigglegram_panel(pools.get("perseverance", []), day)
    spacecraft = sorted({c.spacecraft for c in picks if c.spacecraft})
    intro = INTROS[subject].format(n=len(panels), craft=", ".join(spacecraft) or "public feeds")
    d = Digest(day=day, subject=subject, title=TITLES[subject].format(day=day.isoformat()), intro=intro, panels=panels)
    upsert_digest(d)
    logger.info("digest for %s: %s with %d panels", day, subject, len(panels))
    return d


def _wigglegram_panel(candidates: list[Candidate], day: date) -> list[Panel]:
    """Best effort: a Mastcam-Z stereo pair alternated as a GIF. Nothing qualifies, or anything fails: no panel."""
    try:
        from .publish import survey_candidates  # survey pages (committed) widen the search beyond the daily page-0 feed
        from .sources import SOURCES
        from .wiggle import best_wigglegram  # numpy/Pillow import kept out of the hot path

        source = SOURCES["perseverance"]
        pool = {c.key: c for c in fresh(survey_candidates(source), day, source.freshness_days)}
        pool.update({c.key: c for c in candidates})
        found = best_wigglegram(list(pool.values()), day)
        if not found:
            logger.info("wigglegram: no qualifying Mastcam-Z colour pair among %d candidates", len(pool))
    except Exception:
        logger.exception("wigglegram step failed; skipping")
        return []
    if not found:
        return []
    left, right, rel, _spread, ms = found
    return [
        Panel(
            candidate=left,
            site_image=str(Path("assets/img") / day.isoformat() / Path(rel).name),
            heading=f"Mastcam-Z stereo pair as a wigglegram, sequence {left.meta.get('sequence')}",
            blurb=(
                f"The left and right eyes of Mastcam-Z sit 24 cm apart. Alternating their two frames every {ms} ms, aligned on the "
                "subject, fakes depth without glasses: things nearer or farther than the subject wobble. An old trick called a wigglegram."
            ),
            derived_image=rel,
            derived_from=[left.key, right.key],
        )
    ]


def _panel(c: Candidate, day: date) -> Panel:
    card = card_for(c)
    ext = image_ext(str(c.image_url))
    heading = panel_heading(c, card)
    if card and card.spacecraft_name:
        heading += f" on {card.spacecraft_name}"
    elif c.spacecraft:
        heading += f" on {c.spacecraft}"
    blurb = (card.what_it_sees or card.what_it_is).strip() if card else ""
    return Panel(
        candidate=c,
        site_image=str(Path("assets/img") / day.isoformat() / f"{c.source}-{safe_name(c.source_id)}{ext}"),
        heading=heading,
        blurb=blurb,
    )
