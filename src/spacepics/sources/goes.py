"""GOES-19 (GOES-East) ABI full-disk GeoColor, via NOAA STAR's CDN. No key.

Feed: the directory listing HTML at https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/ (about 1.6 MB, ~10 days
of frames at 10-minute cadence). Filenames are YYYYDDDHHMM_GOES19-ABI-FD-GEOCOLOR-{339x339,678x678,1808x1808,
5424x5424,10848x10848,21696x21696}.jpg where DDD is day of year. Unversioned `latest.jpg` is the 10848 px file
(18 MB): never use. Verified 2026-09-17.

GeoColor is a composite: true color by day, and at night an infrared blend with city lights from a static layer.
"""

import re
from datetime import UTC, datetime, timedelta

import httpx
from pydantic import BaseModel

from ..models import Candidate

LISTING_URL = "https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/"
CREDIT = "NOAA/NESDIS/STAR"
HREF_RE = re.compile(r'href="(\d{4})(\d{3})(\d{2})(\d{2})_GOES19-ABI-FD-GEOCOLOR-678x678\.jpg"')
CADENCE_HOURS = 3
SIZES = {"thumb": "339x339", "preview": "678x678", "display": "1808x1808"}


class RawFrame(BaseModel):
    captured_at: datetime

    def url(self, size: str) -> str:
        return f"{LISTING_URL}{self.captured_at:%Y%j%H%M}_GOES19-ABI-FD-GEOCOLOR-{SIZES[size]}.jpg"


class GoesSource:
    name = "goes"
    subject = "Earth"
    release_tier = "realtime"
    feed_suffix = "html"
    enabled = True
    freshness_days = 2
    weight = 1

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(LISTING_URL)
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        frames = []
        for year, doy, hh, mm in HREF_RE.findall(raw.decode("utf-8", errors="ignore")):
            captured_at = datetime(int(year), 1, 1, int(hh), int(mm), tzinfo=UTC) + timedelta(days=int(doy) - 1)
            frames.append(RawFrame(captured_at=captured_at))
        # earliest frame in each 3-hour bucket per day
        buckets: dict[tuple, RawFrame] = {}
        for f in sorted(frames, key=lambda f: f.captured_at):
            buckets.setdefault((f.captured_at.date(), f.captured_at.hour // CADENCE_HOURS), f)
        return [self._to_candidate(f) for f in buckets.values()]

    def _to_candidate(self, f: RawFrame) -> Candidate:
        return Candidate(
            source=self.name,
            source_id=f"{f.captured_at:%Y%m%dT%H%M}",
            spacecraft="GOES-19",
            instrument="ABI GeoColor",
            captured_at=f.captured_at,
            image_url=f.url("display"),
            preview_url=f.url("preview"),
            thumbnail_url=f.url("thumb"),
            title=f"Earth from GOES-19, GeoColor, {f.captured_at:%Y-%m-%d %H:%M} UTC",
            credit=CREDIT,
            source_page_url="https://www.star.nesdis.noaa.gov/goes/fulldisk.php?sat=G19",
            meta={"product": "GeoColor"},
        )
