"""Pipeline stages. Network stages: fetch, download. Offline stages: extract, pick.

Feeds and candidates are saved to disk between stages so extraction and picking can be
iterated on without touching the source sites again.
"""

import hashlib
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from .models import Candidate, Pick
from .paths import DATA_DIR, FEEDS_DIR, SITE_DIR, images_dir
from .sources import Source
from .store import read_candidates, read_picks, upsert_pick, write_candidates

logger = logging.getLogger(__name__)

USER_AGENT = "spacepics/0.1 (github.com/ktrnka/space-pics; personal daily-image project)"
DEFAULT_FRESHNESS_DAYS = 7


def today() -> date:
    return datetime.now(UTC).date()


def make_client() -> httpx.Client:
    return httpx.Client(timeout=60, follow_redirects=True, headers={"User-Agent": USER_AGENT})


def feed_path(source: Source, day: date) -> Path:
    return FEEDS_DIR / source.name / f"{day.isoformat()}.{source.feed_suffix}"


def fetch(sources: list[Source], day: date) -> list[Path]:
    """Save each source's raw feed verbatim."""
    paths = []
    with make_client() as client:
        for source in sources:
            try:
                raw = source.fetch_feed(client)
            except Exception:
                logger.exception("fetch failed for %s; continuing with the other sources", source.name)
                continue
            path = feed_path(source, day)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            logger.info("fetched %s: %d bytes -> %s", source.name, len(raw), path)
            paths.append(path)
    return paths


def extract(sources: list[Source], day: date | None) -> dict[str, list[Candidate]]:
    """Parse saved feeds into candidates. Uses the latest saved feed per source if no day is given."""
    out = {}
    for source in sources:
        src_dir = FEEDS_DIR / source.name
        path = feed_path(source, day) if day else max(src_dir.glob(f"*.{source.feed_suffix}"), default=None)
        if path is None or not path.exists():
            logger.warning("no saved feed for %s; run fetch first", source.name)
            continue
        try:
            candidates = source.extract(path.read_bytes())
        except Exception:
            logger.exception("extract failed for %s (%s); continuing with the other sources", source.name, path.name)
            continue
        feed_day = date.fromisoformat(path.stem)
        write_candidates(source.name, feed_day, candidates)
        logger.info("extracted %s: %d candidates from %s", source.name, len(candidates), path.name)
        out[source.name] = candidates
    return out


def image_cache_path(url: str) -> Path:
    """Cache keyed by URL so images can be downloaded before an extractor exists for the source."""
    ext = Path(urlsplit(url).path).suffix.lower() or ".jpg"
    return images_dir() / (hashlib.sha1(url.encode()).hexdigest()[:16] + ext)


def download_url(client: httpx.Client, url: str, pause: float = 0.5) -> Path:
    """Fetch one image into the cache if not already there. Sleeps after a real download to stay polite."""
    path = image_cache_path(url)
    if path.exists():
        return path
    resp = client.get(url)
    resp.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    logger.debug("downloaded %s (%d bytes)", url, len(resp.content))
    time.sleep(pause)
    return path


def download(sources: list[Source], limit: int | None) -> int:
    """Fill the preview image cache for the latest candidates. Sequential, to be polite to the hosts."""
    n = 0
    with make_client() as client:
        for source in sources:
            for candidate in read_candidates(source.name)[:limit]:
                download_url(client, str(candidate.preview_url))
                n += 1
    logger.info("downloaded %d preview images", n)
    return n


def fresh(candidates: list[Candidate], day: date, days: int = DEFAULT_FRESHNESS_DAYS) -> list[Candidate]:
    cutoff = datetime.combine(day, datetime.min.time(), tzinfo=UTC) - timedelta(days=days)
    return [c for c in candidates if (c.released_at or c.captured_at) >= cutoff]


@dataclass
class Choice:
    """What a chooser returns. `derived_image` (relative to data/) publishes a locally generated image, e.g. a
    composite, in place of the candidate's own image; `candidate` is then the anchor frame it was built around."""

    candidate: Candidate
    caption: str
    picker: str
    derived_image: str | None = None
    derived_from: list[str] = field(default_factory=list)


Pools = dict[str, list[Candidate]]  # fresh candidates keyed by source name
Chooser = Callable[[list[Source], Pools, date, list[Pick]], Choice]


def choose_random(sources: list[Source], pools: Pools, day: date, previous: list[Pick]) -> Choice:
    """Placeholder chooser: weighted source, then uniform instrument, then uniform frame. Seeded by the day.

    Source weights come from each adapter; within a source, instruments are drawn uniformly so a chatty
    camera doesn't swamp a rare one. Yesterday's source is skipped when there's a choice.
    """
    avoid = previous[-1].candidate.source if previous else None
    weights = {s.name: s.weight for s in sources}
    candidate = stratified_choice(pools, weights, random.Random(day.isoformat()), avoid_source=avoid)
    return Choice(candidate=candidate, caption=default_caption(candidate), picker="random-stratified")


def stratified_choice(pools: Pools, weights: dict[str, float], rng: random.Random, avoid_source: str | None = None) -> Candidate:
    pools = {name: cs for name, cs in pools.items() if cs}
    if not pools:
        raise RuntimeError("no fresh candidates; run fetch and extract first")
    eligible = [name for name in pools if name != avoid_source] or list(pools)
    source_name = rng.choices(eligible, weights=[weights.get(name, 1) for name in eligible])[0]
    by_instrument: dict[str, list[Candidate]] = {}
    for c in pools[source_name]:
        by_instrument.setdefault(c.instrument, []).append(c)
    instrument = rng.choice(sorted(by_instrument))
    return rng.choice(sorted(by_instrument[instrument], key=lambda c: c.key))


def pick(sources: list[Source], day: date, chooser: Chooser = choose_random) -> Pick:
    """Build the day's Pick from a chooser's Choice and record it. Choosers only decide; this persists."""
    pools = {s.name: fresh(read_candidates(s.name), day, s.freshness_days) for s in sources}
    previous = [p for p in read_picks() if p.day < day]
    choice = chooser(sources, pools, day, previous)
    image_name = Path(choice.derived_image).name if choice.derived_image else Path(str(choice.candidate.image_url)).name
    ext = Path(image_name).suffix.lower() or ".jpg"
    result = Pick(
        day=day,
        candidate=choice.candidate,
        caption=choice.caption,
        picker=choice.picker,
        site_image=str(Path("assets/img") / day.isoformat() / f"{choice.candidate.source}-{safe_name(choice.candidate.source_id)}{ext}"),
        derived_image=choice.derived_image,
        derived_from=choice.derived_from,
    )
    upsert_pick(result)
    logger.info("picked %s for %s via %s", choice.candidate.key, day, choice.picker)
    return result


def default_caption(candidate: Candidate) -> str:
    return f"{candidate.title}. Captured {candidate.captured_at:%Y-%m-%d %H:%M} UTC. Credit: {candidate.credit}."


def safe_name(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in s)


def materialize_pick_image(pick: Pick) -> Path:
    """Copy the pick's display image into site/: a derived image from data/, else the candidate's image (downloaded on demand)."""
    dest = SITE_DIR / pick.site_image
    if dest.exists():
        return dest
    if pick.derived_image:
        src = DATA_DIR / pick.derived_image
    else:
        with make_client() as client:
            src = download_url(client, str(pick.candidate.image_url))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return dest
