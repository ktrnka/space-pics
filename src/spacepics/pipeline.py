"""Pipeline stages. Network stages: fetch, download. Offline stages: extract, pick.

Feeds and candidates are saved to disk between stages so extraction and picking can be
iterated on without touching the source sites again.
"""

import logging
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx

from .models import Candidate, Pick
from .paths import FEEDS_DIR, IMAGES_DIR, SITE_IMG_DIR
from .sources import Source
from .store import read_candidates, upsert_pick, write_candidates

logger = logging.getLogger(__name__)

USER_AGENT = "spacepics/0.1 (github.com/ktrnka/space-pics; personal daily-image project)"
FRESHNESS = timedelta(days=7)


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


def image_cache_path(candidate: Candidate, display: bool = False) -> Path:
    url = str(candidate.image_url if display else candidate.preview_url)
    ext = Path(url).suffix.lower() or ".jpg"
    kind = "display" if display else "preview"
    return IMAGES_DIR / candidate.source / f"{candidate.source_id}.{kind}{ext}"


def download_image(client: httpx.Client, candidate: Candidate, display: bool = False) -> Path:
    path = image_cache_path(candidate, display)
    if path.exists():
        return path
    url = str(candidate.image_url if display else candidate.preview_url)
    resp = client.get(url)
    resp.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return path


def download(sources: list[Source], limit: int | None) -> int:
    """Fill the preview image cache for the latest candidates. Sequential, to be polite to the hosts."""
    n = 0
    with make_client() as client:
        for source in sources:
            for candidate in read_candidates(source.name)[:limit]:
                download_image(client, candidate)
                n += 1
    logger.info("downloaded %d preview images", n)
    return n


def fresh(candidates: list[Candidate], day: date) -> list[Candidate]:
    cutoff = datetime.combine(day, datetime.min.time(), tzinfo=UTC) - FRESHNESS
    return [c for c in candidates if c.captured_at >= cutoff]


def pick_random(sources: list[Source], day: date) -> Pick:
    """Placeholder picker: a seeded random choice among recent candidates. Replaced by ranking + VLM later."""
    pool = []
    for source in sources:
        pool.extend(fresh(read_candidates(source.name), day))
    if not pool:
        raise RuntimeError("no fresh candidates; run fetch and extract first")
    candidate = random.Random(day.isoformat()).choice(pool)
    ext = Path(str(candidate.image_url)).suffix.lower() or ".jpg"
    pick = Pick(
        day=day,
        candidate=candidate,
        caption=default_caption(candidate),
        picker="random",
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
        src = download_image(client, pick.candidate, display=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return dest
