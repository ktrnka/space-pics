"""Write site outputs: one Jekyll post per pick, and plain-HTML debug galleries per source/instrument.

Debug galleries are plain HTML (no Jekyll needed) so they can be opened straight from disk
while iterating on a source. They link to remote images rather than copying them.
"""

import logging
from collections import defaultdict
from datetime import date
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .models import Pick
from .paths import DEBUG_DIR, POSTS_DIR
from .pipeline import materialize_pick_image
from .sources import Source
from .store import read_candidates, read_picks

logger = logging.getLogger(__name__)

env = Environment(loader=PackageLoader("spacepics", "templates"), autoescape=select_autoescape(["html"]), keep_trailing_newline=True)


def post_path(pick: Pick) -> Path:
    return POSTS_DIR / f"{pick.day.isoformat()}-{pick.candidate.source}.md"


def write_post(pick: Pick) -> Path:
    materialize_pick_image(pick)
    path = post_path(pick)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(env.get_template("post.md.j2").render(pick=pick))
    return path


def publish(day: date | None) -> list[Path]:
    """Write posts for every pick (idempotent). Restrict to one day if given."""
    picks = [p for p in read_picks() if day is None or p.day == day]
    paths = [write_post(p) for p in picks]
    logger.info("wrote %d posts", len(paths))
    return paths


def write_debug_galleries(sources: list[Source], per_instrument_limit: int = 60) -> list[Path]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for source in sources:
        by_instrument = defaultdict(list)
        for c in sorted(read_candidates(source.name), key=lambda c: c.captured_at, reverse=True):
            by_instrument[c.instrument].append(c)
        groups = {k: v[:per_instrument_limit] for k, v in sorted(by_instrument.items())}
        path = DEBUG_DIR / f"{source.name}.html"
        path.write_text(env.get_template("gallery.html.j2").render(source=source.name, groups=groups))
        paths.append(path)
    index = DEBUG_DIR / "index.html"
    index.write_text(env.get_template("debug_index.html.j2").render(sources=[s.name for s in sources]))
    paths.append(index)
    return paths
