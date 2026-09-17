"""NASA Astronomy Picture of the Day. Curated, so a fallback rather than the point. Needs NASA_API_KEY.

Feed: https://api.nasa.gov/planetary/apod returns one JSON object: date, title, explanation, url, hdurl,
media_type (image or video: skip videos), copyright.

Quirk: `copyright` (when present) is written for display and often has newlines and stray runs of
whitespace, e.g. "ESA/Webb, NASA & CSA, M. Reiter; Acknowledgement: M. H. \\xd6zsara\\xe7\\n Text: \\nCecilia
Chirenti \\n(NASA\\nGSFC, \\nUMCP, \\nCRESST II)". Collapsed to one line for `credit`; falls back to "NASA APOD"
when the field is absent (public-domain NASA/government images).
"""

import os
from datetime import UTC, date, datetime

import httpx
from pydantic import BaseModel, HttpUrl

from ..models import Candidate

API_URL = "https://api.nasa.gov/planetary/apod"
DEFAULT_CREDIT = "NASA APOD"


class RawApod(BaseModel):
    """The feed is a single object, not a list."""

    date: str  # "YYYY-MM-DD"
    title: str
    explanation: str
    url: HttpUrl
    hdurl: HttpUrl | None = None
    media_type: str  # "image" or "video"
    copyright: str | None = None


class ApodSource:
    name = "apod"
    subject = "Various"
    feed_suffix = "json"
    enabled = True
    freshness_days = 3  # one curated image a day; fallback only
    weight = 0.5

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(API_URL, params={"api_key": os.environ.get("NASA_API_KEY", "DEMO_KEY")})
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        item = RawApod.model_validate_json(raw)
        if item.media_type != "image":
            return []
        day = date.fromisoformat(item.date)
        return [
            Candidate(
                source=self.name,
                source_id=item.date,
                instrument=self.name,
                captured_at=datetime.combine(day, datetime.min.time(), tzinfo=UTC),
                image_url=item.url,  # hdurl can be a multi-MB original; the display copy lives in the repo
                preview_url=item.url,
                title=item.title,
                credit=_clean_credit(item.copyright),
                source_page_url=f"https://apod.nasa.gov/apod/ap{day:%y%m%d}.html",
                meta={"explanation": item.explanation, "hdurl": str(item.hdurl) if item.hdurl else None},
            )
        ]


def _clean_credit(copyright_: str | None) -> str:
    if not copyright_:
        return DEFAULT_CREDIT
    collapsed = " ".join(copyright_.split())
    return collapsed or DEFAULT_CREDIT
