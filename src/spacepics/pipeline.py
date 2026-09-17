"""Pipeline stages. Network stages: fetch, download. Offline stages: extract, pick.

Feeds and candidates are saved to disk between stages so extraction and picking can be
iterated on without touching the source sites again.
"""

import hashlib
import logging
import random
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from .models import Candidate, Pick
from .paths import FEEDS_DIR, IMAGES_DIR, SITE_IMG_DIR
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
            raw = source.fetch_feed(client)
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
        candidates = source.extract(path.read_bytes())
        feed_day = date.fromisoformat(path.stem)
        write_candidates(source.name, feed_day, candidates)
        logger.info("extracted %s: %d candidates from %s", source.name, len(candidates), path.name)
        out[source.name] = candidates
    return out


def image_cache_path(url: str) -> Path:
    """Cache keyed by URL so images can be downloaded before an extractor exists for the source."""
    ext = Path(urlsplit(url).path).suffix.lower() or ".jpg"
    return IMAGES_DIR / (hashlib.sha1(url.encode()).hexdigest()[:16] + ext)


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
    return [c for c in candidates if c.captured_at >= cutoff]


# Placeholder weighting until the ranker exists. Raw-feed sources outweigh curated ones because raw frames are
# the point of the project; within a source, instruments are drawn uniformly so a chatty camera doesn't swamp a rare one.
SOURCE_WEIGHTS = {"perseverance": 3, "sdo": 2, "esa_webb": 2, "esa_hubble": 2, "epic": 1, "hirise": 1, "apod": 0.5}


def stratified_choice(pools: dict[str, list[Candidate]], rng: random.Random, avoid_source: str | None = None) -> Candidate:
    """Weighted source, then uniform instrument, then uniform frame. Skips yesterday's source when there's a choice."""
    pools = {name: cs for name, cs in pools.items() if cs}
    if not pools:
        raise RuntimeError("no fresh candidates; run fetch and extract first")
    eligible = [name for name in pools if name != avoid_source] or list(pools)
    source_name = rng.choices(eligible, weights=[SOURCE_WEIGHTS.get(name, 1) for name in eligible])[0]
    by_instrument: dict[str, list[Candidate]] = {}
    for c in pools[source_name]:
        by_instrument.setdefault(c.instrument, []).append(c)
    instrument = rng.choice(sorted(by_instrument))
    return rng.choice(sorted(by_instrument[instrument], key=lambda c: c.key))


def pick_random(sources: list[Source], day: date) -> Pick:
    """Placeholder picker: seeded stratified random choice among fresh candidates. Replaced by ranking + VLM later."""
    pools = {s.name: fresh(read_candidates(s.name), day, getattr(s, "freshness_days", DEFAULT_FRESHNESS_DAYS)) for s in sources}
    previous = [p for p in read_picks() if p.day < day]
    avoid = previous[-1].candidate.source if previous else None
    candidate = stratified_choice(pools, random.Random(day.isoformat()), avoid_source=avoid)
    ext = Path(str(candidate.image_url)).suffix.lower() or ".jpg"
    pick = Pick(
        day=day,
        candidate=candidate,
        caption=default_caption(candidate),
        picker="random-stratified",
        site_image=str(Path("assets/img") / day.isoformat() / f"{candidate.source}-{safe_name(candidate.source_id)}{ext}"),
    )
    upsert_pick(pick)
    logger.info("picked %s for %s", candidate.key, day)
    return pick


def default_caption(candidate: Candidate) -> str:
    return f"{candidate.title}. Captured {candidate.captured_at:%Y-%m-%d %H:%M} UTC. Credit: {candidate.credit}."


def safe_name(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in s)


def materialize_pick_image(pick: Pick) -> Path:
    """Copy the pick's display image into site/. Downloads it if the cache doesn't have it."""
    dest = SITE_IMG_DIR.parent.parent / pick.site_image
    if dest.exists():
        return dest
    with make_client() as client:
        src = download_url(client, str(pick.candidate.image_url))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return dest
