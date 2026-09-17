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
from .pipeline import fresh, safe_name
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
    picks = []
    for ch in ("0304", "0171", "211193171", "HMIIC"):
        frames = _by(sdo, instrument=ch)
        if frames:  # the frame nearest noon UTC
            picks.append(min(frames, key=lambda c: abs(c.captured_at.hour - 12)))
    hv = pools.get("helioviewer", [])
    for inst in ("SOHO LASCO C2", "GOES SUVI", "STEREO-A EUVI", "PROBA-2 SWAP"):
        frames = _by(hv, instrument=inst)
        if frames:
            picks += _pick(rng, frames, 1)
    return picks


def recipe_earth(rng: random.Random, pools: dict[str, list[Candidate]]) -> list[Candidate]:
    picks = []
    goes = pools.get("goes", [])
    if goes:
        newest_day = max(c.captured_at.date() for c in goes)
        day_frames = [c for c in goes if c.captured_at.date() == newest_day]
        picks += sorted(day_frames, key=lambda c: c.captured_at)[:: max(1, len(day_frames) // 3)][:3]
    picks += _pick(rng, pools.get("epic", []), 2)
    return picks


RECIPES = {"Mars": recipe_mars, "Sun": recipe_sun, "Earth": recipe_earth}
TITLES = {"Mars": "Mars, {day}", "Sun": "The Sun, {day}", "Earth": "Earth, {day}"}


def build_digest(sources: list[Source], day: date) -> Digest:
    pools = {s.name: fresh(read_candidates(s.name), day, s.freshness_days) for s in sources}
    subjects = {s.subject for s in sources if pools[s.name]}
    subject = choose_subject(day, subjects & set(ROTATION))
    rng = random.Random(f"{day.isoformat()}:{subject}")
    picks = RECIPES[subject](rng, {s.name: pools[s.name] for s in sources if s.subject == subject})[:MAX_PANELS]
    if not picks:
        raise RuntimeError(f"recipe for {subject} produced no panels")
    panels = [_panel(c, day) for c in picks]
    spacecraft = sorted({c.spacecraft for c in picks if c.spacecraft})
    captured = max(c.captured_at for c in picks).date()
    noun = {"Sun": "the Sun", "Mars": "Mars", "Earth": "Earth"}[subject]
    intro = f"{len(panels)} recent images of {noun} from {', '.join(spacecraft) or 'public feeds'}."
    d = Digest(day=day, subject=subject, title=TITLES[subject].format(day=captured.isoformat()), intro=intro, panels=panels)
    upsert_digest(d)
    logger.info("digest for %s: %s with %d panels", day, subject, len(panels))
    return d


def _panel(c: Candidate, day: date) -> Panel:
    card = card_for(c)
    ext = Path(str(c.image_url)).suffix.lower() or ".jpg"
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
