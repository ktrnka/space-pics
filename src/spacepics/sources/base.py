from typing import Protocol

import httpx

from ..models import Candidate


class Source(Protocol):
    """A feed of recent images.

    Two halves, deliberately split so extraction can be developed and tested offline
    against saved feeds in data/feeds/ and tests/fixtures/:

    - fetch_feed: network only. Returns the raw response bytes to be saved verbatim.
    - extract: pure. Parses raw bytes into Candidates. No network, no filesystem.
    """

    name: str
    subject: str  # what the images are of, for grouping galleries: "Sun", "Earth", "Mars", "Deep space", "Various"
    feed_suffix: str  # file extension for the saved feed, e.g. "json", "xml", "html"
    enabled: bool  # False while extract() is unimplemented; the daily job only runs enabled sources
    freshness_days: int  # how old a candidate may be and still be picked; weekly/monthly sources need more than daily ones
    weight: float  # relative chance of this source being chosen by the placeholder picker (raw feeds > curated)

    def fetch_feed(self, client: httpx.Client) -> bytes: ...

    def extract(self, raw: bytes) -> list[Candidate]: ...
