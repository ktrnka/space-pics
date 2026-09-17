"""NOIRLab image of the week (Gemini, Blanco, Kitt Peak, and Rubin press images). No key. Curated, weekly.

Feed: RSS 2.0 at https://noirlab.edu/public/images/iotw/feed/, 25 items, each with an <enclosure> pointing at the
screen-size JPEG (about 100-500 KB), a link to the image page, and a pubDate. Verified 2026-09-17.

Credit is fixed at NOIRLab/NSF/AURA: the RSS feed doesn't carry the per-image facility and photographer line that
NOIRLab's own image pages show, so ours is intentionally generic and the post links to the page.
"""

from datetime import UTC
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

from ..models import Candidate

FEED_URL = "https://noirlab.edu/public/images/iotw/feed/"
CREDIT = "NOIRLab/NSF/AURA"


class NoirlabSource:
    name = "noirlab"
    subject = "Deep space"
    release_tier = "curated"
    feed_suffix = "xml"
    enabled = True
    freshness_days = 10
    weight = 1

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(FEED_URL)
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        out = []
        for item in ElementTree.fromstring(raw).findall("./channel/item"):
            enclosure = item.find("enclosure")
            link = (item.findtext("link") or "").strip()
            pub = item.findtext("pubDate")
            if enclosure is None or not link or not pub:
                continue
            image_url = enclosure.attrib["url"]
            out.append(
                Candidate(
                    source=self.name,
                    source_id=link.rstrip("/").rsplit("/", 1)[-1],
                    spacecraft=None,
                    instrument="iotw",
                    captured_at=parsedate_to_datetime(pub).astimezone(UTC),
                    image_url=image_url,
                    preview_url=image_url,
                    title=(item.findtext("title") or "").strip(),
                    credit=CREDIT,
                    source_page_url=link,
                    meta={"description": " ".join(ElementTree.fromstring(f"<d>{item.findtext('description') or ''}</d>").itertext()).strip()[:500]},
                )
            )
        return out
