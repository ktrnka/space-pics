from .base import Source
from .perseverance import PerseveranceSource

SOURCES: dict[str, Source] = {s.name: s for s in [PerseveranceSource()]}


def get_sources(names: tuple[str, ...] | None = None) -> list[Source]:
    if not names:
        return list(SOURCES.values())
    return [SOURCES[n] for n in names]
