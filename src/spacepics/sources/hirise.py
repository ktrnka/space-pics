"""HiRISE picture of the day (Mars Reconnaissance Orbiter). No key.

Feed: RSS 0.91 at https://www.uahirise.org/togo/rss.php, one item per HiPOD; was empty on one fetch
during research and populated on another, so treat as best effort. Full products are gigapixel JPEG2000:
only use the feed's small JPEG.

Quirks (from the saved 2026-09-17 feed, one item):
- No per-item `pubDate`; only the channel has one ("Thu, 17 Sep 2026 10:47:19 MST"). Every item in a
  fetch therefore gets the same `captured_at` (the channel's pubDate, i.e. roughly the fetch/publish
  time, not necessarily the observation time). If an item ever does carry its own pubDate we prefer it.
  If neither is present (channel malformed) the item is dropped rather than guessing a date.
- The image URL and a human-readable credit line live inside `description`, which is a blob of HTML
  (an <img> tag, caption text, and a trailing "(NASA/JPL-Caltech/University of Arizona)" credit).
  We pull the <img src=...> for the image and use a fixed credit string rather than trying to
  parse it back out of the caption text.
- `title` is prefixed "HiPOD: "; stripped for display.
"""

import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from ..models import Candidate

FEED_URL = "https://www.uahirise.org/togo/rss.php"
CREDIT = "NASA/JPL-Caltech/University of Arizona"
TITLE_PREFIX = "HiPOD: "

_IMG_SRC_RE = re.compile(r"<img[^>]*\bsrc=['\"]([^'\"]+)['\"]", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


class HiriseSource:
    name = "hirise"
    feed_suffix = "xml"
    enabled = True
    freshness_days = 7  # roughly daily
    weight = 1

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(FEED_URL)
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        root = ElementTree.fromstring(raw)
        channel = root.find("channel")
        if channel is None:
            return []
        channel_pub_date = _parse_pub_date(channel.findtext("pubDate"))

        candidates = []
        for item in channel.findall("item"):
            link = (item.findtext("link") or "").strip()
            description = item.findtext("description") or ""
            image_url = _find_image_url(description)
            captured_at = _parse_pub_date(item.findtext("pubDate")) or channel_pub_date
            if not link or not image_url or captured_at is None:
                continue

            title = (item.findtext("title") or "").strip()
            title = title.removeprefix(TITLE_PREFIX)

            candidates.append(
                Candidate(
                    source=self.name,
                    source_id=link.rstrip("/").rsplit("/", 1)[-1],
                    instrument=self.name,
                    captured_at=captured_at,
                    image_url=image_url,
                    preview_url=image_url,
                    title=title,
                    credit=CREDIT,
                    source_page_url=link,
                    meta={"description": _strip_tags(description)},
                )
            )
        return candidates


def _find_image_url(description: str) -> str | None:
    match = _IMG_SRC_RE.search(description)
    return match.group(1) if match else None


def _strip_tags(text: str) -> str:
    return " ".join(_TAG_RE.sub(" ", text).split())


def _parse_pub_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except TypeError, ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
