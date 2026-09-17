"""Many solar observatories through one API: Helioviewer (api.helioviewer.org/v2). No key.

Verified 2026-09-17:
- getDataSources lists every layer with a numeric sourceId and its latest date ("end").
- getClosestImage?date=...&sourceId=N returns metadata for the nearest frame: its real `date`, native `scale`
  (arcsec/px), `width`, `height`. Cheap; no image.
- takeScreenshot?date=...&imageScale=S&layers=[N,1,100]&x0=0&y0=0&width=W&height=H&display=true&watermark=false
  renders a PNG server-side (~700 KB at 1024 px). Fitting the whole native frame into W px means
  imageScale = scale * native_width / W. Each call is a render, so keep counts small and paced.

fetch_feed writes a MANIFEST (JSON) rather than a feed: one entry per layer with the closest-image metadata and
the screenshot URLs to use. The download and publish stages then hit takeScreenshot through the URL-keyed cache.

Embargo made visible: Solar Orbiter EUI's latest frames are from 2025-01 (about 8 months behind), so getClosestImage
for "today" returns January; captured_at carries the real date and freshness drops it until the archive catches up.
SOHO EIT lags about 3 weeks. GOES SUVI, LASCO, STEREO-A, PROBA-2, Hinode XRT, GONG, KCor are within days.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from ..models import Candidate

API = "https://api.helioviewer.org/v2"
CREDIT = "Helioviewer.org; data courtesy of the respective instrument teams"


@dataclass(frozen=True)
class Layer:
    source_id: int
    spacecraft: str
    instrument: str  # instrument (and detector) name used as the grouping key
    measurement: str  # wavelength in Å, or e.g. "white-light"


LAYERS = [
    Layer(4, "SOHO", "LASCO C2", "white-light"),
    Layer(5, "SOHO", "LASCO C3", "white-light"),
    Layer(0, "SOHO", "EIT", "171"),
    Layer(1, "SOHO", "EIT", "195"),
    Layer(2, "SOHO", "EIT", "284"),
    Layer(3, "SOHO", "EIT", "304"),
    Layer(20, "STEREO-A", "EUVI", "171"),
    Layer(21, "STEREO-A", "EUVI", "195"),
    Layer(22, "STEREO-A", "EUVI", "284"),
    Layer(23, "STEREO-A", "EUVI", "304"),
    Layer(28, "STEREO-A", "COR1", "white-light"),
    Layer(29, "STEREO-A", "COR2", "white-light"),
    Layer(32, "PROBA-2", "SWAP", "174"),
    Layer(2000, "GOES", "SUVI", "94"),
    Layer(2001, "GOES", "SUVI", "131"),
    Layer(2002, "GOES", "SUVI", "171"),
    Layer(2003, "GOES", "SUVI", "195"),
    Layer(2004, "GOES", "SUVI", "284"),
    Layer(2005, "GOES", "SUVI", "304"),
    Layer(132, "GOES", "CCOR-1", "white-light"),
    Layer(94, "GONG", "H-alpha", "6562"),
    Layer(83, "MLSO", "KCor", "735"),
    Layer(10001, "Hinode", "XRT", "any"),
    Layer(84, "Solar Orbiter", "EUI FSI", "174"),
    Layer(85, "Solar Orbiter", "EUI FSI", "304"),
    Layer(86, "Solar Orbiter", "EUI HRI", "174"),
    Layer(87, "Solar Orbiter", "EUI HRI", "1216"),
    Layer(503, "Solar Orbiter", "SoloHI", "difference"),
    Layer(131, "PUNCH", "WFI+NFI", "total brightness"),
]
REQUEST_HOUR_UTC = 12
DISPLAY_PX = 1024
PREVIEW_PX = 512


def screenshot_url(source_id: int, when: datetime, native_scale: float, native_width: int, size: int) -> str:
    params = {
        "date": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "imageScale": round(native_scale * native_width / size, 4),
        "layers": f"[{source_id},1,100]",
        "x0": 0,
        "y0": 0,
        "width": size,
        "height": size,
        "display": "true",
        "watermark": "false",
    }
    return f"{API}/takeScreenshot/?{urlencode(params)}"


class HelioviewerSource:
    name = "helioviewer"
    subject = "Sun"
    release_tier = "realtime"  # per layer it varies; Solar Orbiter is effectively "delayed" (see docstring)
    feed_suffix = "json"
    enabled = True
    freshness_days = 3
    weight = 2

    def fetch_feed(self, client: httpx.Client) -> bytes:
        """One getClosestImage per layer at noon UTC today; the manifest records what came back."""
        when = datetime.now(UTC).replace(hour=REQUEST_HOUR_UTC, minute=0, second=0, microsecond=0)
        entries = []
        for layer in LAYERS:
            resp = client.get(f"{API}/getClosestImage/", params={"date": when.strftime("%Y-%m-%dT%H:%M:%SZ"), "sourceId": layer.source_id})
            if resp.status_code != 200:
                entries.append({**asdict(layer), "error": resp.status_code})
                continue
            closest = resp.json()
            actual = datetime.strptime(closest["date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            entries.append(
                {
                    **asdict(layer),
                    "closest": closest,
                    "display_url": screenshot_url(layer.source_id, actual, closest["scale"], closest["width"], DISPLAY_PX),
                    "preview_url": screenshot_url(layer.source_id, actual, closest["scale"], closest["width"], PREVIEW_PX),
                }
            )
            time.sleep(0.5)
        manifest = {"requested_for": when.isoformat(), "fetched_at": datetime.now(UTC).isoformat(), "layers": entries}
        return json.dumps(manifest, indent=1).encode()

    def extract(self, raw: bytes) -> list[Candidate]:
        manifest = json.loads(raw)
        out = []
        for e in manifest["layers"]:
            closest = e.get("closest")
            if not closest:
                continue
            captured_at = datetime.strptime(closest["date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            instrument = f"{e['spacecraft']} {e['instrument']}"
            out.append(
                Candidate(
                    source=self.name,
                    source_id=f"{e['source_id']}-{captured_at:%Y%m%dT%H%M%S}",
                    spacecraft=e["spacecraft"],
                    instrument=instrument,
                    captured_at=captured_at,
                    image_url=e["display_url"],
                    preview_url=e["preview_url"],
                    title=f"{instrument} {e['measurement']}" + (" Å" if e["measurement"].isdigit() else ""),
                    credit=CREDIT,
                    source_page_url=f"https://helioviewer.org/?date={captured_at:%Y-%m-%dT%H:%M:%S}Z",
                    meta={
                        "helioviewer_source_id": e["source_id"],
                        "measurement": e["measurement"],
                        "native_scale_arcsec_px": closest.get("scale"),
                        "native_width": closest.get("width"),
                        "lag_days": round((datetime.fromisoformat(manifest["requested_for"]) - captured_at).total_seconds() / 86400, 1),
                    },
                )
            )
        return out
