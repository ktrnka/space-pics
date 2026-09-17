"""Hand-maintained reference cards (data/reference/instruments/*.yaml) and readable metadata for posts."""

import logging
from datetime import datetime
from functools import cache
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from .models import Candidate
from .paths import DATA_DIR

logger = logging.getLogger(__name__)

CARDS_DIR = DATA_DIR / "reference" / "instruments"

# Labels for meta keys that mean the same thing everywhere; cards can add or override per instrument.
COMMON_META_LABELS = {
    "sol": "Sol (Mars day of the mission)",
    "sequence": "Observation sequence",
    "filter_name": "Filter",
    "product": "Product type",
    "channel": "Channel",
    "wavelength_angstrom": "Wavelength (Å)",
    "measurement": "Measurement",
    "lag_days": "Days between request and newest available frame",
    "mast_az": "Mast azimuth (°)",
    "mast_el": "Mast elevation (°)",
    "lmst": "Local mean solar time",
    "centroid_lat": "Sub-satellite latitude (°)",
    "centroid_lon": "Sub-satellite longitude (°)",
    "ra": "Right ascension (°)",
    "dec": "Declination (°)",
    "fov": "Field of view (arcmin)",
    "constellation": "Constellation",
    "object": "Object",
    "release_id": "Release",
}
HIDDEN_META = {"description", "explanation", "hdurl", "helioviewer_source_id", "native_scale_arcsec_px", "native_width", "size", "version"}


class Link(BaseModel):
    title: str
    url: str


class Card(BaseModel):
    spacecraft: str | None = None
    instruments: list[str]
    name: str
    spacecraft_name: str | None = None
    operator: str | None = None
    what_it_is: str = ""
    what_it_sees: str = ""
    why_it_matters: str = ""
    reading_the_image: str = ""
    wikipedia: str | None = None
    spacecraft_wikipedia: str | None = None
    links: list[Link] = []
    meta_labels: dict[str, str] = {}
    picture_types: list[str] = []
    confidence: str = "from-memory"


@cache
def load_cards() -> dict[tuple[str | None, str], Card]:
    """(spacecraft, instrument) -> Card. Missing or malformed files are skipped so a bad card never blocks a post."""
    out: dict[tuple[str | None, str], Card] = {}
    for path in sorted(CARDS_DIR.glob("*.yaml")):
        try:
            entries = yaml.safe_load(path.read_text()) or []
        except yaml.YAMLError:
            logger.exception("unreadable card file %s", path)
            continue
        for entry in entries:
            try:
                card = Card.model_validate(entry)
            except ValidationError as ex:
                logger.warning("skipping malformed card in %s: %s", path.name, ex)
                continue
            for inst in card.instruments:
                out[(card.spacecraft, inst)] = card
    return out


def card_for(candidate: Candidate) -> Card | None:
    cards = load_cards()
    return cards.get((candidate.spacecraft, candidate.instrument)) or cards.get((None, candidate.instrument))


def readable_meta(candidate: Candidate, card: Card | None = None) -> list[tuple[str, str]]:
    """Labelled, human-readable metadata lines for a post. Unknown keys get a tidied version of the key name."""
    labels = {**COMMON_META_LABELS, **(card.meta_labels if card else {})}
    lines = [("Captured", f"{candidate.captured_at:%Y-%m-%d %H:%M} UTC")]
    if candidate.released_at:
        lines.append(("Released", f"{candidate.released_at:%Y-%m-%d}"))
    for key, value in candidate.meta.items():
        if key in HIDDEN_META or value in (None, "", [], {}):
            continue
        lines.append((labels.get(key, key.replace("_", " ").capitalize()), _fmt(value)))
    return lines


def _fmt(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{k.replace('_', ' ')} {_fmt(v)}" for k, v in value.items())
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, datetime):
        return f"{value:%Y-%m-%d %H:%M} UTC"
    return str(value)
