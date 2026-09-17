"""Hand-maintained reference cards (data/reference/instruments/*.yaml) and readable metadata for posts."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from functools import cache
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from .models import Candidate
from .paths import DATA_DIR

logger = logging.getLogger(__name__)

CARDS_DIR = DATA_DIR / "reference" / "instruments"

# Meta keys shown in a panel caption: key -> (short label, tooltip definition). Cards can add or override.
# Keys not listed here are left for the full "Image details" table, never the caption.
CAPTION_KEYS: dict[str, tuple[str, str]] = {
    "sol": ("Sol", "A Mars day counted from the rover's landing; a sol is 24 h 39 min"),
    "sequence": ("Sequence", "One commanded observation; frames sharing a sequence id were taken together (a filter set, a mosaic)"),
    "product": ("", "Product type as published in the raw feed"),
    "lmst": ("Local time", "Local mean solar time at the rover"),
    "wavelength_angstrom": ("", "Wavelength of the emission line this channel isolates"),
    "lag_days": ("Lag", "Days between the requested time and the newest frame the archive had; long lags mean an embargo"),
    "centroid_lat": ("Lat", "Latitude of the point directly below the spacecraft"),
    "centroid_lon": ("Lon", "Longitude of the point directly below the spacecraft"),
    "ra": ("RA", "Right ascension of the field centre, degrees"),
    "dec": ("Dec", "Declination of the field centre, degrees"),
    "constellation": ("", "Constellation the field lies in"),
    "object": ("", "Target object"),
}
# Human words for raw values. Applied by key; a "*" entry is a fallback pattern applied to any value.
VALUE_LABELS: dict[str, dict[str, str]] = {
    "product": {"ECM": "Processed image", "EBY": "Raw Bayer frame", "EJP": "JPEG product"},
}
FILTER_NM = re.compile(r"_(\d{3,4})NM")
# Full "Image details" table (single-image posts): longer labels for every key we know, and keys never worth showing.
COMMON_META_LABELS = {k: (label or k.capitalize()) for k, (label, _tip) in CAPTION_KEYS.items()} | {
    "filter_name": "Filter",
    "channel": "Channel",
    "measurement": "Measurement",
    "mast_az": "Mast azimuth (°)",
    "mast_el": "Mast elevation (°)",
    "fov": "Field of view (arcmin)",
    "release_id": "Release",
}
HIDDEN_META = {"description", "explanation", "hdurl", "helioviewer_source_id", "native_scale_arcsec_px", "native_width", "size", "version"}


def value_label(key: str, value: Any, card: Card | None = None) -> str:
    """Colloquial rendering of a raw meta value: 'Processed image' for ECM, 'colour' for an RGB filter, '866 nm' for a band."""
    text = str(value)
    for table in ((card.value_labels.get(key, {}) if card else {}), VALUE_LABELS.get(key, {})):
        if text in table:
            return table[text]
    if key == "filter_name":
        if text.endswith("RGB"):
            return "colour"
        if m := FILTER_NM.search(text):
            return f"{m.group(1)} nm"
    if key == "wavelength_angstrom":
        return f"{text} Å"
    return _fmt(value)


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
    formal_name: str | None = None  # the long official name, shown once in the card text for reference
    instrument_labels: dict[str, str] = {}  # instrument value -> colloquial detail for headings, e.g. MCZ_LEFT: "left eye"
    value_labels: dict[str, dict[str, str]] = {}  # meta key -> raw value -> colloquial label
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


def caption_items(candidate: Candidate, card: Card | None = None) -> list[tuple[str, str, str]]:
    """(label, value, tooltip) for the one-line panel caption. Only CAPTION_KEYS, only when present."""
    items = []
    for key, (label, tooltip) in CAPTION_KEYS.items():
        value = candidate.meta.get(key)
        if value in (None, "", [], {}):
            continue
        if key == "lag_days":
            if abs(float(value)) < 1:
                continue
            value = f"{int(round(float(value)))} days"
        items.append((label, value_label(key, value, card), tooltip))
    return items


def panel_heading(candidate: Candidate, card: Card | None = None) -> str:
    """Colloquial heading: card name, then instrument detail and filter when the card spans several, e.g. 'Mastcam-Z, left eye, colour'."""
    if card is None:
        return candidate.instrument
    parts = [card.name]
    if len(card.instruments) > 1 and candidate.instrument in card.instrument_labels:
        parts.append(card.instrument_labels[candidate.instrument])
    filt = candidate.meta.get("filter_name")
    if filt and filt != "OPEN":
        parts.append(value_label("filter_name", filt, card))
    elif candidate.meta.get("wavelength_angstrom"):
        parts.append(value_label("wavelength_angstrom", candidate.meta["wavelength_angstrom"], card))
    elif str(candidate.meta.get("measurement", "")).isdigit() and len(card.instruments) > 1:
        parts.append(f"{candidate.meta['measurement']} Å")
    return ", ".join(p for p in parts if p)


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
