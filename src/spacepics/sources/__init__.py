from .apod import ApodSource
from .base import Source
from .curiosity import CuriositySource
from .epic import EpicSource
from .esa import EsaSource
from .helioviewer import HelioviewerSource
from .hirise import HiriseSource
from .perseverance import PerseveranceSource
from .sdo import SdoSource

ALL_SOURCES: list[Source] = [
    PerseveranceSource(),
    CuriositySource(),
    SdoSource(),
    HelioviewerSource(),
    EsaSource("esa_webb", "https://esawebb.org", "potm"),
    EsaSource("esa_hubble", "https://esahubble.org", "potw"),
    EpicSource(),
    ApodSource(),
    HiriseSource(),
]
SOURCES: dict[str, Source] = {s.name: s for s in ALL_SOURCES}


def get_sources(names: tuple[str, ...] | None = None) -> list[Source]:
    """Enabled sources by default; explicit names may include disabled ones (for developing a source)."""
    if not names:
        return [s for s in ALL_SOURCES if s.enabled]
    return [SOURCES[n] for n in names]
