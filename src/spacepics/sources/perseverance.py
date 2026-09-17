"""Perseverance (Mars 2020) raw image feed. No API key.

Feed: https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json
Hundreds of frames per sol. Mastcam-Z frames carry a per-filter name (e.g. ZCAM_R2_866NM),
which is what makes this the multispectral-composite source later.
"""

from datetime import UTC, datetime

import httpx
from pydantic import BaseModel, HttpUrl

from ..models import Candidate

FEED_URL = "https://mars.nasa.gov/rss/api/"
# The docs write order=sol+desc; a literal '+' gets percent-encoded and the API then 302s to an HTML page.
# A space (encoded %20) is accepted.
FEED_PARAMS = {"feed": "raw_images", "category": "mars2020", "feedtype": "json", "order": "sol desc", "page": 0}
DEFAULT_NUM = 100  # the API caps a page at 100 regardless of num
CREDIT = "NASA/JPL-Caltech"


class RawImageFiles(BaseModel):
    small: HttpUrl  # ~320 px
    medium: HttpUrl  # ~800 px
    large: HttpUrl  # ~1200 px
    full_res: HttpUrl  # PNG, avoid


class RawCamera(BaseModel):
    instrument: str
    filter_name: str | None = None


class RawImage(BaseModel):
    """One item of the feed's `images` array. Only the fields we use; the feed has many more."""

    imageid: str
    sol: int
    date_taken_utc: str  # "2026-09-17T04:59:26.915", naive but UTC
    sample_type: str  # "Full" or "Thumbnail"
    camera: RawCamera
    image_files: RawImageFiles
    title: str | None = None


class RawFeed(BaseModel):
    images: list[RawImage]
    total_results: int


class PerseveranceSource:
    name = "perseverance"
    feed_suffix = "json"

    def __init__(self, num: int = DEFAULT_NUM):
        self.num = num

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(FEED_URL, params={**FEED_PARAMS, "num": self.num})
        resp.raise_for_status()
        if "json" not in resp.headers.get("content-type", ""):
            raise RuntimeError(f"expected JSON from {resp.url}, got {resp.headers.get('content-type')}")
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        feed = RawFeed.model_validate_json(raw)
        return [self._to_candidate(img) for img in feed.images if img.sample_type == "Full"]

    def _to_candidate(self, img: RawImage) -> Candidate:
        captured_at = datetime.fromisoformat(img.date_taken_utc).replace(tzinfo=UTC)
        filter_name = None if img.camera.filter_name in (None, "UNK") else img.camera.filter_name
        title = f"Perseverance {img.camera.instrument}, sol {img.sol}"
        if filter_name:
            title += f", filter {filter_name}"
        return Candidate(
            source=self.name,
            source_id=img.imageid,
            instrument=img.camera.instrument,
            captured_at=captured_at,
            image_url=img.image_files.large,
            preview_url=img.image_files.medium,
            title=title,
            credit=CREDIT,
            source_page_url=f"https://mars.nasa.gov/mars2020/multimedia/raw-images/{img.imageid}",
            meta={"sol": img.sol, "filter_name": filter_name},
        )
