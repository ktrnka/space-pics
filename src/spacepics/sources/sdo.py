"""SDO (Solar Dynamics Observatory) browse archive. No key.

Feed: the directory listing HTML at https://sdo.gsfc.nasa.gov/assets/img/browse/YYYY/MM/DD/ (about 1.2 MB),
which lists date-stamped files like 20260917_173710_1024_0171.jpg for every channel, roughly every 7 minutes.
Use these stable URLs, not assets/img/latest/ (same URL, changing bytes).

Channels: AIA 0094 0131 0171 0193 0211 0304 0335 1600 1700 4500; HMI HMIB HMIBC HMIIC HMIIF HMII HMID;
composites 211193171 (and 'n', 'rg' variants), 304211171, HMI171. Sizes: 512, 1024, 2048, 4096.
"""

from datetime import UTC, date, datetime

import httpx

from ..models import Candidate

BROWSE_URL = "https://sdo.gsfc.nasa.gov/assets/img/browse/{y:04d}/{m:02d}/{d:02d}/"
CREDIT = "NASA/SDO and the AIA, EVE, and HMI science teams"

# Channels worth showing, and a 3-hourly cadence, keep candidates to roughly 80-90 per day.
CHANNELS = ["0094", "0131", "0171", "0193", "0211", "0304", "0335", "1600", "1700", "HMIIC", "211193171"]
CADENCE_HOURS = 3


class SdoSource:
    name = "sdo"
    feed_suffix = "html"
    enabled = False

    def __init__(self, day: date | None = None):
        self.day = day

    def fetch_feed(self, client: httpx.Client) -> bytes:
        day = self.day or datetime.now(UTC).date()
        resp = client.get(BROWSE_URL.format(y=day.year, m=day.month, d=day.day))
        resp.raise_for_status()
        return resp.content

    def extract(self, raw: bytes) -> list[Candidate]:
        raise NotImplementedError("see docs/TASKS.md: Source: SDO")
