"""Curiosity (MSL) raw images via the newer mars.nasa.gov API. No key.

Feed: https://mars.nasa.gov/api/v1/raw_image_items/?order=sol desc&per_page=100&page=0&condition_1=msl:mission
(the older rss/api?category=msl endpoint returns "No more images"). Verified 2026-09-17: JSON with `items`,
`more`, `total`, `page`, `per_page`. Items carry `imageid`, `sol`, `instrument` (e.g. MAST_LEFT, NAVCAM_RIGHT_B,
CHEMCAM_RMI, MAHLI, FHAZ_*), `date_taken` (ISO, Z), `https_url` (full-size JPEG), `is_thumbnail`, `image_credit`,
and `extended.url_list` (per-size variants). As with Perseverance, a literal '+' in `order` breaks the request; send a space.
"""

import httpx

from ..models import Candidate

FEED_URL = "https://mars.nasa.gov/api/v1/raw_image_items/"
FEED_PARAMS = {"order": "sol desc", "page": 0, "condition_1": "msl:mission"}
DEFAULT_PER_PAGE = 100
CREDIT = "NASA/JPL-Caltech"


class CuriositySource:
    name = "curiosity"
    subject = "Mars"
    release_tier = "realtime"
    feed_suffix = "json"
    enabled = False
    freshness_days = 7
    weight = 2

    def __init__(self, per_page: int = DEFAULT_PER_PAGE):
        self.per_page = per_page

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(FEED_URL, params={**FEED_PARAMS, "per_page": self.per_page})
        resp.raise_for_status()
        if "json" not in resp.headers.get("content-type", ""):
            raise RuntimeError(f"expected JSON from {resp.url}, got {resp.headers.get('content-type')}")
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        raise NotImplementedError("see docs/TASKS.md: Source: Curiosity")
