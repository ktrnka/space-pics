"""Cross-source models. Each source keeps its own raw models; only Candidate crosses the boundary."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, HttpUrl


class Candidate(BaseModel):
    """One image that could be the pick of the day, in a source-independent shape.

    Sources map their own raw records into this. Anything source-specific that later
    stages might want (filter name, sol, RA/Dec) goes in `meta` rather than becoming a field.
    """

    source: str  # adapter (feed) name, e.g. "perseverance", "helioviewer"; one adapter may cover several spacecraft
    source_id: str  # stable within the source
    spacecraft: str | None = None  # the vehicle, e.g. "Perseverance", "SDO", "SOHO"; None when it varies or is unknown (APOD)
    instrument: str  # grouping key for per-instrument ranking and galleries
    captured_at: datetime  # when the image was taken; UTC, tz-aware
    released_at: datetime | None = None  # when it became public, for embargoed sources; freshness uses this when set
    image_url: HttpUrl  # display-size image (roughly 1000-2000 px)
    preview_url: HttpUrl  # smaller image for embedding/ranking; may equal image_url
    thumbnail_url: HttpUrl | None = None  # tiny image for wide galleries (roughly 300-500 px); galleries fall back to preview_url
    title: str
    credit: str
    source_page_url: HttpUrl | None = None
    meta: dict[str, Any] = {}

    @property
    def key(self) -> str:
        return f"{self.source}:{self.source_id}"


class Pick(BaseModel):
    """The published image for one day."""

    day: date
    candidate: Candidate  # the source frame; for a composite, the anchor frame it was built around
    caption: str
    picker: str  # how it was chosen, e.g. "random-stratified", "vlm:claude-opus-5", "composite:mastcam-z"
    site_image: str  # path relative to site/, e.g. "assets/img/2026-09-17/perseverance-abc.jpg"
    derived_image: str | None = None  # path relative to data/ of a locally generated image to publish instead of candidate.image_url
    derived_from: list[str] = []  # candidate keys a derived image was built from
