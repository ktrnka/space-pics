"""ESA/Webb picture of the month and ESA/Hubble picture of the week. No key.

List feed: {host}/images/{potm|potw}/json/ returns the 20 most recent releases with every image size
under formats_url (screen ~1280 px, screen640, large, thumb700x, ... originals are TIFF: never use).
Per-image API: {host}/images/{image_id}/api/json/ (note: image id like potm2608a, not release id potm2608)
carries RA/Dec, field of view, constellation, credit. fetch_feed saves both: the list plus per-image
JSON for the newest few, combined into one JSON document {"list": [...], "images": {image_id: {...}}}.

Quirks found while writing extract():

- A release may have no still image at all (a before/after slider: `image` is null, `comparison` is set
  instead). Skip those; there's nothing to build a Candidate around.
- The per-image detail JSON is AVM (Astronomy Visualisation Metadata) with dotted keys, e.g.
  `Spatial.ReferenceValue` = [RA, Dec] in decimal degrees, `Spatial.ReferenceDimension` = [width, height]
  in pixels, `Spatial.Scale` = [x, y] degrees/pixel. Field of view is dimension * |scale|. Constellation
  and object name aren't separate structured fields; `Subject.Name` sometimes carries an object name, and
  constellation only ever shows up as a word inside the free-text `Description`.
- Text fields in that same detail JSON (`Credit`, `Title`, `Description`, ...) come through as the
  *Python repr of a bytes object* baked into the JSON string, e.g. `"b'ESA/Webb, NASA & CSA, A. Leroy'"`
  or with backslash-escaped UTF-8 bytes for non-ASCII punctuation. `ast.literal_eval` on the string
  followed by `.decode("utf-8")` recovers the real text; this is exactly a Python bytes literal, so that
  round-trips cleanly instead of needing a hand-rolled unescaper.
- The Hubble POTW list's newest entry is dated 2025-12-29 as of this fetch (2026-09-17): the feed is
  either stale or the weekly series has paused. Do not "fix" this; extract just maps whatever the saved
  feed contains.
"""

import ast
import json
import re
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from ..models import Candidate

DETAIL_COUNT = 3  # per-image JSON only for the newest few; that's all the freshness window will use

DEFAULT_CREDIT = {
    "webb": "ESA/Webb, NASA, CSA",
    "hubble": "ESA/Hubble & NASA",
}

# "...lies in the constellation Leo at..." / "...constellation Cetus (the Whale)..."
CONSTELLATION_RE = re.compile(r"constellations?\s+(?:of\s+)?([A-Z][a-zA-Z]+)")
FIRST_SENTENCE_RE = re.compile(r"(.+?[.!?])(\s|$)")


class FormatsUrl(BaseModel):
    """Only the two sizes extract() uses; the feed carries a couple dozen more (wallpapers, zoomable, ...)."""

    model_config = ConfigDict(extra="allow")

    screen: HttpUrl  # ~1280 px, used as image_url
    screen640: HttpUrl  # used as preview_url


class ListEntry(BaseModel):
    """One item of the list feed's top-level array. Only the fields extract() uses."""

    id: str  # release id, e.g. "potm2608" (no trailing letter)
    release_date: str  # naive, "2026-08-27T10:00:00", UTC
    title: str
    description: str  # HTML; not used (see module docstring on messiness / the detail JSON's plain-text copy)
    image: str | None = None  # e.g. "potm2608a"; null for a release with no still image (a comparison slider)
    category: str
    formats_url: FormatsUrl


class ImageDetail(BaseModel):
    """Per-image AVM metadata, loosely: dotted keys, and most text fields are bytes-repr strings (see
    module docstring). Only what extract() maps into Candidate.meta; everything else is allowed through."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    credit: str | None = Field(None, alias="Credit")
    description: str | None = Field(None, alias="Description")
    subject_name: list[str] | None = Field(None, alias="Subject.Name")
    ra_dec: list[str] | None = Field(None, alias="Spatial.ReferenceValue")  # [RA, Dec], decimal degrees
    dimension_px: list[str] | None = Field(None, alias="Spatial.ReferenceDimension")  # [width, height] px
    scale_deg_per_px: list[str] | None = Field(None, alias="Spatial.Scale")  # [x, y] degrees/px, signed


class RawFeed(BaseModel):
    entries: list[ListEntry] = Field(alias="list")
    images: dict[str, ImageDetail]


def _decode_avm_text(value: str | None) -> str | None:
    """Undo the bytes-repr-in-JSON quirk (see module docstring). Falls back to the raw string if it
    isn't shaped like a Python bytes literal."""
    if not value:
        return None
    if value.startswith(("b'", 'b"')):
        try:
            decoded = ast.literal_eval(value)
        except ValueError:
            return value
        except SyntaxError:
            return value
        if isinstance(decoded, bytes):
            try:
                return decoded.decode("utf-8")
            except UnicodeDecodeError:
                return value
    return value


def _first_sentence(text: str) -> str | None:
    match = FIRST_SENTENCE_RE.match(text.strip())
    return match.group(1) if match else None


class EsaSource:
    feed_suffix = "json"
    enabled = True
    freshness_days = 45  # monthly (potm) and weekly (potw) releases

    def __init__(self, name: str, host: str, list_name: str):
        self.name = name
        self.host = host
        self.list_name = list_name

    def fetch_feed(self, client: httpx.Client) -> bytes:
        resp = client.get(f"{self.host}/images/{self.list_name}/json/")
        resp.raise_for_status()
        entries = resp.json()
        images = {}
        for entry in entries[:DETAIL_COUNT]:
            image_id = entry["image"]
            time.sleep(1)
            detail = client.get(f"{self.host}/images/{image_id}/api/json/")
            if detail.status_code == 200:
                images[image_id] = detail.json()
        return json.dumps({"list": entries, "images": images}, indent=1).encode()

    def extract(self, raw: bytes) -> list[Candidate]:
        feed = RawFeed.model_validate_json(raw)
        return [self._to_candidate(entry, feed.images.get(entry.image)) for entry in feed.entries if entry.image]

    def _to_candidate(self, entry: ListEntry, detail: ImageDetail | None) -> Candidate:
        instrument = self.name.removeprefix("esa_")  # "webb" or "hubble"
        captured_at = datetime.fromisoformat(entry.release_date).replace(tzinfo=UTC)
        credit = DEFAULT_CREDIT[instrument]
        meta: dict[str, Any] = {
            "release_id": entry.id,
            "ra": None,
            "dec": None,
            "fov": None,
            "constellation": None,
            "object": None,
        }
        if detail is not None:
            decoded_credit = _decode_avm_text(detail.credit)
            if decoded_credit:
                credit = decoded_credit
            if detail.ra_dec and len(detail.ra_dec) == 2:
                meta["ra"] = float(detail.ra_dec[0])
                meta["dec"] = float(detail.ra_dec[1])
            if detail.dimension_px and detail.scale_deg_per_px and len(detail.dimension_px) == 2 and len(detail.scale_deg_per_px) == 2:
                width_arcmin = abs(float(detail.dimension_px[0]) * float(detail.scale_deg_per_px[0])) * 60
                height_arcmin = abs(float(detail.dimension_px[1]) * float(detail.scale_deg_per_px[1])) * 60
                meta["fov"] = {"width_arcmin": round(width_arcmin, 2), "height_arcmin": round(height_arcmin, 2)}
            if detail.subject_name:
                meta["object"] = detail.subject_name[0]
            decoded_description = _decode_avm_text(detail.description)
            if decoded_description:
                constellation_match = CONSTELLATION_RE.search(decoded_description)
                if constellation_match:
                    meta["constellation"] = constellation_match.group(1)
                first_sentence = _first_sentence(decoded_description)
                if first_sentence:
                    meta["description"] = first_sentence
        return Candidate(
            source=self.name,
            source_id=entry.image,
            instrument=instrument,
            captured_at=captured_at,
            image_url=entry.formats_url.screen,
            preview_url=entry.formats_url.screen640,
            title=entry.title,
            credit=credit,
            source_page_url=f"{self.host}/images/{entry.image}/",
            meta=meta,
        )
