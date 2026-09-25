"""Curiosity (MSL) raw images via the newer mars.nasa.gov API. No key.

Feed: https://mars.nasa.gov/api/v1/raw_image_items/?order=sol desc&per_page=100&page=0&condition_1=msl:mission
(the older rss/api?category=msl endpoint returns "No more images"). Verified 2026-09-17: JSON with `items`,
`more`, `total`, `page`, `per_page`. Items carry `imageid`, `sol`, `instrument` (e.g. MAST_LEFT, NAV_RIGHT_B,
CHEMCAM_RMI, MAHLI, FHAZ_*), `date_taken` (ISO, Z), `https_url` (full-size JPEG), `is_thumbnail`, `image_credit`,
`title`, `link`, and `extended` (a dict; may carry `url_list`, `mast_az`, `mast_el`, `lmst`).
As with Perseverance, a literal '+' in `order` breaks the request; send a space.

Quirk: on the 2026-09-17 feed, `extended.url_list` is a single URL string identical to `https_url`, not a
dict/list of size variants as the older MSL API docs suggest. No smaller image is available, so
`preview_url` falls back to `image_url` (== `https_url`) for every item.

Quirk: `link` is always feed-relative (e.g. "/raw_images/1639694"), never absolute, on the observed feed.
`source_page_url` is only set when `link` looks absolute; otherwise it's None.
"""

import re
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel

from ..models import Candidate

FEED_URL = "https://mars.nasa.gov/api/v1/raw_image_items/"
FEED_PARAMS = {"order": "sol desc", "page": 0, "condition_1": "msl:mission"}
DEFAULT_PER_PAGE = 100
CREDIT = "NASA/JPL-Caltech"
# imageid like NRB_842870462EDR_S1250198NCAM00594M_: the trailing NCAM00594 is the sequence (one observation).
SEQUENCE_RE = re.compile(r"([A-Z]{3,4}\d{5})M?_?$")


class RawExtended(BaseModel):
    """Only the fields we use; the feed's `extended` dict has more (bucket, contributor, sample_type, ...)."""

    url_list: str | None = None
    mast_az: str | None = None
    mast_el: str | None = None
    lmst: str | None = None


class RawImage(BaseModel):
    """One item of the feed's `items` array. Only the fields we use; the feed has many more."""

    imageid: str
    sol: int
    instrument: str
    date_taken: str  # "2026-09-16T23:31:21.000Z"
    https_url: str
    is_thumbnail: bool
    image_credit: str | None = None
    title: str | None = None
    link: str | None = None
    extended: RawExtended = RawExtended()


class RawFeed(BaseModel):
    items: list[RawImage]
    total: int


class CuriositySource:
    name = "curiosity"
    subject = "Mars"
    release_tier = "realtime"
    feed_suffix = "json"
    enabled = True
    freshness_days = 7
    weight = 2
    gallery_layout = "sequence"

    def __init__(self, per_page: int = DEFAULT_PER_PAGE):
        self.per_page = per_page

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(FEED_URL, params={**FEED_PARAMS, "per_page": self.per_page})
        resp.raise_for_status()
        if "json" not in resp.headers.get("content-type", ""):
            raise RuntimeError(f"expected JSON from {resp.url}, got {resp.headers.get('content-type')}")
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        feed = RawFeed.model_validate_json(raw)
        return [self._to_candidate(img) for img in feed.items if not img.is_thumbnail]

    def _to_candidate(self, img: RawImage) -> Candidate:
        captured_at = datetime.fromisoformat(img.date_taken).astimezone(UTC)
        source_page_url = img.link if img.link and img.link.startswith(("http://", "https://")) else None
        # url_list has never offered a smaller variant on the observed feed (always == https_url); fall
        # back to the full-size image rather than assume a size convention that hasn't been seen.
        preview_url = img.extended.url_list if img.extended.url_list else img.https_url
        return Candidate(
            source=self.name,
            source_id=img.imageid,
            spacecraft="Curiosity",
            instrument=img.instrument,
            captured_at=captured_at,
            image_url=img.https_url,
            preview_url=preview_url,
            title=f"Curiosity {img.instrument}, sol {img.sol}",
            credit=img.image_credit or CREDIT,
            source_page_url=source_page_url,
            meta={
                "sol": img.sol,
                "sequence": (sm.group(1) if (sm := SEQUENCE_RE.search(img.imageid)) else None),
                "mast_az": img.extended.mast_az,
                "mast_el": img.extended.mast_el,
                "lmst": img.extended.lmst,
            },
        )
