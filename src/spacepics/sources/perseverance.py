"""Perseverance (Mars 2020) raw image feed. No API key.

Feed: https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json
Hundreds of frames per sol. Mastcam-Z frames carry a per-filter name (e.g. ZCAM_R2_866NM),
which is what makes this the multispectral-composite source later.
"""

import json
import re
import time
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel, HttpUrl

from ..models import Candidate

FEED_URL = "https://mars.nasa.gov/rss/api/"
# The docs write order=sol+desc; a literal '+' gets percent-encoded and the API then 302s to an HTML page.
# A space (encoded %20) is accepted.
FEED_PARAMS = {"feed": "raw_images", "category": "mars2020", "feedtype": "json", "order": "sol desc", "page": 0}
DEFAULT_NUM = 100  # the API caps a page at 100 regardless of num
# Page 0 alone is often one sol of navcam tiles and misses that sol's Mastcam-Z colour frames (2026-09-17 to 09-21).
DEFAULT_PAGES = 4
PAGE_PAUSE_S = 1.0
CREDIT = "NASA/JPL-Caltech"
# imageid like ZR2_1982_0842891670_957ECM_N0910970ZCAM03022_100085J: the sequence id (ZCAM03022) names one observation,
# e.g. a multispectral filter set of the same scene or the tiles of a navcam panorama.
SEQUENCE_RE = re.compile(r"_N\d+([A-Z]{3,4}\d{5})")
# Fourth field like 957ECM: product type. ECM = processed image, EBY = raw Bayer frame, EJP = JPEG.
PRODUCT_RE = re.compile(r"^[A-Z0-9]+_\d+_\d+_\d{3}([A-Z]{3})")
# Position 0 (L0/R0) is the Bayer color filter, i.e. an ordinary RGB image; positions 1-6 are narrowband science
# filters (see data/reference/instruments/mars.yaml). The shared predicate for "a Mastcam-Z color frame": digest.py's
# panel recipe and wiggle.py's stereo pairing both need it and used to filter differently.
MASTCAM_INSTRUMENTS = ("MCZ_LEFT", "MCZ_RIGHT")
MASTCAM_COLOR_FILTERS = frozenset({"ZCAM_L0_RGB", "ZCAM_R0_RGB"})


def is_mastcam_color(c: Candidate) -> bool:
    """True for a Mastcam-Z Bayer-color (L0/R0) frame, left or right eye."""
    return c.instrument in MASTCAM_INSTRUMENTS and c.meta.get("filter_name") in MASTCAM_COLOR_FILTERS


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
    subject = "Mars"
    release_tier = "realtime"
    feed_suffix = "json"
    enabled = True
    freshness_days = 7
    weight = 3
    gallery_layout = "sequence"

    def __init__(self, num: int = DEFAULT_NUM, pages: int = DEFAULT_PAGES):
        self.num = num
        self.pages = pages

    def fetch_feed(self, client: httpx.Client) -> bytes:
        """Pages 0..pages-1 merged into one response shaped like a single page, so extract and the saved-feed layout don't change."""
        merged: dict | None = None
        seen: set[str] = set()
        for page in range(self.pages):
            if page:
                time.sleep(PAGE_PAUSE_S)
            resp = client.get(FEED_URL, params={**FEED_PARAMS, "num": self.num, "page": page})
            resp.raise_for_status()
            if "json" not in resp.headers.get("content-type", ""):
                raise RuntimeError(f"expected JSON from {resp.url}, got {resp.headers.get('content-type')}")
            body = resp.json()
            if merged is None:
                merged = {**body, "images": [], "pages_fetched": 0}
            new = [img for img in body.get("images", []) if img.get("imageid") not in seen]  # the feed can shift between requests
            seen.update(img.get("imageid") for img in new)
            merged["images"].extend(new)
            merged["pages_fetched"] = page + 1
            if len(body.get("images", [])) < self.num:
                break
        return json.dumps(merged).encode()

    def extract(self, raw: bytes) -> list[Candidate]:
        feed = RawFeed.model_validate_json(raw)
        return [self._to_candidate(img) for img in feed.images if self._wanted(img)]

    @staticmethod
    def _wanted(img: RawImage) -> bool:
        """Full frames only; drop raw Bayer products (EBY duplicates the processed ECM frame as a grey checkerboard)
        and the neutral-density solar-filter frames (L7/R7: a small sun disc on black, for atmospheric opacity)."""
        product = m.group(1) if (m := PRODUCT_RE.search(img.imageid)) else None
        solar_filter = bool(img.camera.filter_name and "_ND" in img.camera.filter_name)
        return img.sample_type == "Full" and product != "EBY" and not solar_filter

    def _to_candidate(self, img: RawImage) -> Candidate:
        captured_at = datetime.fromisoformat(img.date_taken_utc).replace(tzinfo=UTC)
        filter_name = None if img.camera.filter_name in (None, "UNK") else img.camera.filter_name
        title = f"Perseverance {img.camera.instrument}, sol {img.sol}"
        if filter_name:
            title += f", filter {filter_name}"
        return Candidate(
            source=self.name,
            source_id=img.imageid,
            spacecraft="Perseverance",
            instrument=img.camera.instrument,
            captured_at=captured_at,
            image_url=img.image_files.large,
            preview_url=img.image_files.medium,
            thumbnail_url=img.image_files.small,
            title=title,
            credit=CREDIT,
            source_page_url=f"https://mars.nasa.gov/mars2020/multimedia/raw-images/{img.imageid}",
            meta={
                "sol": img.sol,
                "filter_name": filter_name,
                "product": (m.group(1) if (m := PRODUCT_RE.search(img.imageid)) else None),
                "sequence": (m.group(1) if (m := SEQUENCE_RE.search(img.imageid)) else None),
            },
        )
