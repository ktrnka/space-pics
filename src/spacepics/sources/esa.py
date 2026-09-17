"""ESA/Webb picture of the month and ESA/Hubble picture of the week. No key.

List feed: {host}/images/{potm|potw}/json/ returns the 20 most recent releases with every image size
under formats_url (screen ~1280 px, screen640, large, thumb700x, ... originals are TIFF: never use).
Per-image API: {host}/images/{image_id}/api/json/ (note: image id like potm2608a, not release id potm2608)
carries RA/Dec, field of view, constellation, credit. fetch_feed saves both: the list plus per-image
JSON for the newest few, combined into one JSON document {"list": [...], "images": {image_id: {...}}}.
"""

import json
import time

import httpx

from ..models import Candidate

DETAIL_COUNT = 3  # per-image JSON only for the newest few; that's all the freshness window will use


class EsaSource:
    feed_suffix = "json"
    enabled = False

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
        raise NotImplementedError("see docs/TASKS.md: Source: ESA")
