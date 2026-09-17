"""SDO (Solar Dynamics Observatory) browse archive. No key.

Feed: the directory listing HTML at https://sdo.gsfc.nasa.gov/assets/img/browse/YYYY/MM/DD/ (about 1.2 MB),
which lists date-stamped files like 20260917_173710_1024_0171.jpg for every channel, roughly every 7 minutes.
Use these stable URLs, not assets/img/latest/ (same URL, changing bytes).

Channels: AIA 0094 0131 0171 0193 0211 0304 0335 1600 1700 4500; HMI HMIB HMIBC HMIIC HMIIF HMII HMID;
composites 211193171 (and 'n', 'rg' variants), 304211171, HMI171. Sizes: 512, 1024, 2048, 4096.
"""

import re
from datetime import UTC, date, datetime

import httpx
from pydantic import BaseModel

from ..models import Candidate

BROWSE_URL = "https://sdo.gsfc.nasa.gov/assets/img/browse/{y:04d}/{m:02d}/{d:02d}/"
CREDIT = "NASA/SDO and the AIA, EVE, and HMI science teams"

# Channels worth showing, and a 3-hourly cadence, keep candidates to roughly 80-90 per day.
CHANNELS = ["0094", "0131", "0171", "0193", "0211", "0304", "0335", "1600", "1700", "HMIIC", "211193171"]
CADENCE_HOURS = 3

# Channels whose name isn't a bare wavelength in angstroms.
CHANNEL_NAMES = {
    "HMIIC": "SDO HMI intensitygram",
    "211193171": "SDO AIA 211/193/171 composite",
}

# Directory-listing hrefs look like 20260917_173710_1024_0171.jpg: date, time, pixel size, channel.
HREF_RE = re.compile(r'href="(\d{8})_(\d{6})_(\d+)_([A-Za-z0-9]+)\.jpg"')

DISPLAY_SIZE = "1024"
IMAGE_SIZE = "2048"


class RawFrame(BaseModel):
    """One parsed href from the directory listing."""

    captured_at: datetime
    size: int
    channel: str

    @property
    def stem(self) -> str:
        return f"{self.captured_at:%Y%m%d_%H%M%S}_{self.size}_{self.channel}"


def _parse_frames(raw: bytes) -> list[RawFrame]:
    frames = []
    for date_str, time_str, size_str, channel in HREF_RE.findall(raw.decode("utf-8", errors="ignore")):
        captured_at = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S").replace(tzinfo=UTC)
        frames.append(RawFrame(captured_at=captured_at, size=int(size_str), channel=channel))
    return frames


def _title(channel: str) -> str:
    if channel in CHANNEL_NAMES:
        return CHANNEL_NAMES[channel]
    if channel.isdigit():
        return f"SDO AIA {int(channel)} Å"
    return f"SDO {channel}"


def _wavelength(channel: str) -> int | None:
    return int(channel) if channel.isdigit() and len(channel) <= 4 else None  # composites like 211193171 are not a wavelength


class SdoSource:
    name = "sdo"
    subject = "Sun"
    release_tier = "realtime"
    feed_suffix = "html"
    enabled = True
    freshness_days = 2  # the daily listing; older days are separate listings we never fetch
    weight = 2

    def __init__(self, day: date | None = None):
        self.day = day

    def fetch_feed(self, client: httpx.Client) -> bytes:
        day = self.day or datetime.now(UTC).date()
        resp = client.get(BROWSE_URL.format(y=day.year, m=day.month, d=day.day))
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        frames = [f for f in _parse_frames(raw) if f.size == int(DISPLAY_SIZE) and f.channel in CHANNELS]

        by_channel: dict[str, dict[int, RawFrame]] = {}
        for frame in frames:
            bucket = frame.captured_at.hour // CADENCE_HOURS
            slots = by_channel.setdefault(frame.channel, {})
            existing = slots.get(bucket)
            if existing is None or frame.captured_at < existing.captured_at:
                slots[bucket] = frame

        candidates = []
        for channel in CHANNELS:
            for bucket in sorted(by_channel.get(channel, {})):
                candidates.append(self._to_candidate(by_channel[channel][bucket]))
        return candidates

    def _to_candidate(self, frame: RawFrame) -> Candidate:
        y, m, d = frame.captured_at.year, frame.captured_at.month, frame.captured_at.day
        base = BROWSE_URL.format(y=y, m=m, d=d)
        preview_name = f"{frame.stem}.jpg"
        image_name = preview_name.replace(f"_{DISPLAY_SIZE}_", f"_{IMAGE_SIZE}_")
        return Candidate(
            source=self.name,
            source_id=frame.stem,
            spacecraft="SDO",
            instrument=frame.channel,
            captured_at=frame.captured_at,
            image_url=base + image_name,
            preview_url=base + preview_name,
            thumbnail_url=base + preview_name.replace(f"_{DISPLAY_SIZE}_", "_512_"),
            title=_title(frame.channel),
            credit=CREDIT,
            source_page_url="https://sdo.gsfc.nasa.gov/data/",
            meta={"channel": frame.channel, "size": int(DISPLAY_SIZE), "wavelength_angstrom": _wavelength(frame.channel)},
        )
