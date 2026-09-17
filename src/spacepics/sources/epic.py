"""NASA EPIC (DSCOVR) whole-Earth natural colour images. Needs NASA_API_KEY (DEMO_KEY works at low volume).

Feed: https://api.nasa.gov/EPIC/api/natural returns the most recent day's images (10-20), each with an
`image` name and `date`. Image URL pattern (verified 2026-09-17):
https://epic.gsfc.nasa.gov/archive/natural/YYYY/MM/DD/jpg/{image}.jpg  (about 1080 px, ~200 KB)
thumbs/ variant is 5 KB, too small for anything. png/ is 2048 px and a few MB: don't use.
Latest available day lags real time by several days.
"""

import os

import httpx

from ..models import Candidate

API_URL = "https://api.nasa.gov/EPIC/api/natural"
CREDIT = "NASA EPIC / DSCOVR"


class EpicSource:
    name = "epic"
    feed_suffix = "json"
    enabled = False

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(API_URL, params={"api_key": os.environ.get("NASA_API_KEY", "DEMO_KEY")})
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        raise NotImplementedError("see docs/TASKS.md: Source: EPIC")
