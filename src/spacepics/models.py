"""Cross-source models. Each source keeps its own raw models; only Candidate crosses the boundary."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, HttpUrl


class Candidate(BaseModel):
    """One image that could be the pick of the day, in a source-independent shape.

    Sources map their own raw records into this. Anything source-specific that later
    stages might want (filter name, sol, RA/Dec) goes in `meta` rather than becoming a field.
    """

    source: str  # adapter name, e.g. "perseverance"
    source_id: str  # stable within the source; used for the image cache filename
    instrument: str  # grouping key for per-instrument ranking and debug galleries
    captured_at: datetime  # UTC, tz-aware
    image_url: HttpUrl  # display-size image (roughly 1000-2000 px)
    preview_url: HttpUrl  # smaller image for embedding/ranking; may equal image_url
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
    candidate: Candidate
    caption: str
    picker: str  # how it was chosen, e.g. "random", "vlm:claude-opus-5"
    site_image: str  # path relative to site/, e.g. "assets/img/2026-09-17/perseverance-abc.jpg"
