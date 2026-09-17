"""NASA Astronomy Picture of the Day. Curated, so a fallback rather than the point. Needs NASA_API_KEY.

Feed: https://api.nasa.gov/planetary/apod returns one JSON object: date, title, explanation, url, hdurl,
media_type (image or video: skip videos), copyright.
"""

import os

import httpx

from ..models import Candidate

API_URL = "https://api.nasa.gov/planetary/apod"


class ApodSource:
    name = "apod"
    feed_suffix = "json"
    enabled = False

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(API_URL, params={"api_key": os.environ.get("NASA_API_KEY", "DEMO_KEY")})
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        raise NotImplementedError("see docs/TASKS.md: Source: APOD")
