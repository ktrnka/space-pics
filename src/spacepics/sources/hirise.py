"""HiRISE picture of the day (Mars Reconnaissance Orbiter). No key.

Feed: RSS 0.91 at https://www.uahirise.org/togo/rss.php, one item per HiPOD; was empty on one fetch
during research and populated on another, so treat as best effort. Full products are gigapixel JPEG2000:
only use the feed's small JPEG.
"""

import httpx

from ..models import Candidate

FEED_URL = "https://www.uahirise.org/togo/rss.php"
CREDIT = "NASA/JPL-Caltech/University of Arizona"


class HiriseSource:
    name = "hirise"
    feed_suffix = "xml"
    enabled = False

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(FEED_URL)
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        raise NotImplementedError("see docs/TASKS.md: Source: HiRISE")
