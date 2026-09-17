"""NASA EPIC (DSCOVR) whole-Earth natural colour images. Needs NASA_API_KEY (DEMO_KEY works at low volume).

Feed: https://api.nasa.gov/EPIC/api/natural returns the most recent day's images (10-20), each with an
`image` name and `date`. Image URL pattern (verified 2026-09-17):
https://epic.gsfc.nasa.gov/archive/natural/YYYY/MM/DD/jpg/{image}.jpg  (about 1080 px, ~200 KB)
thumbs/ variant is 5 KB, too small for anything. png/ is 2048 px and a few MB: don't use.
Latest available day lags real time by several days.
"""

import os
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel, TypeAdapter

from ..models import Candidate

API_URL = "https://api.nasa.gov/EPIC/api/natural"
CREDIT = "NASA EPIC / DSCOVR"
SOURCE_PAGE_URL = "https://epic.gsfc.nasa.gov/"


class RawCentroid(BaseModel):
    lat: float
    lon: float


class RawRecord(BaseModel):
    """One item of the feed's top-level array. Only the fields we use; the feed has many more
    (dscovr/lunar/sun j2000 positions, attitude quaternions, a duplicate `coords` block)."""

    identifier: str
    image: str
    version: str
    date: str  # "YYYY-MM-DD HH:MM:SS", naive but UTC
    centroid_coordinates: RawCentroid


RAW_RECORDS = TypeAdapter(list[RawRecord])


class EpicSource:
    name = "epic"
    subject = "Earth"
    feed_suffix = "json"
    enabled = True
    freshness_days = 10  # latest available day lags real time by several days
    weight = 1

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(API_URL, params={"api_key": os.environ.get("NASA_API_KEY", "DEMO_KEY")})
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        records = RAW_RECORDS.validate_json(raw)
        return [self._to_candidate(rec) for rec in records]

    def _to_candidate(self, rec: RawRecord) -> Candidate:
        captured_at = datetime.strptime(rec.date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{captured_at:%Y/%m/%d}/jpg/{rec.image}.jpg"
        lat, lon = rec.centroid_coordinates.lat, rec.centroid_coordinates.lon
        ns = "N" if lat >= 0 else "S"
        ew = "E" if lon >= 0 else "W"
        title = f"Earth from DSCOVR, centred on {abs(lat):.1f}°{ns} {abs(lon):.1f}°{ew}"
        return Candidate(
            source=self.name,
            source_id=rec.identifier,
            instrument="epic_natural",
            captured_at=captured_at,
            image_url=image_url,
            preview_url=image_url,
            title=title,
            credit=CREDIT,
            source_page_url=SOURCE_PAGE_URL,
            meta={"centroid_lat": lat, "centroid_lon": lon, "version": rec.version},
        )
