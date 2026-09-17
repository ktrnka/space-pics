"""Write site outputs: one Jekyll post per pick, and plain-HTML debug galleries per source/instrument.

Debug galleries are plain HTML (no Jekyll needed) so they can be opened straight from disk
while iterating on a source. They link to remote images rather than copying them.
"""

import logging
from collections import defaultdict
from datetime import date
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .models import Candidate, Pick
from .paths import DEBUG_DIR, POSTS_DIR, SURVEY_DIR
from .pipeline import image_cache_path, materialize_pick_image, safe_name
from .reference import card_for, readable_meta
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
    card = card_for(pick.candidate)
    path.write_text(env.get_template("post.md.j2").render(pick=pick, card=card, meta_lines=readable_meta(pick.candidate, card)))
    return path


def publish(day: date | None) -> list[Path]:
    """Write posts for every pick (idempotent). Restrict to one day if given."""
    picks = [p for p in read_picks() if day is None or p.day == day]
    paths = [write_post(p) for p in picks]
    logger.info("wrote %d posts", len(paths))
    return paths


def survey_candidates(source: Source) -> list[Candidate]:
    """Extra candidates from data/survey/<source>/ feeds (exploration fetches), run through the same extractor."""
    out: list[Candidate] = []
    for f in sorted((SURVEY_DIR / source.name).glob(f"*.{source.feed_suffix}")):
        try:
            out.extend(source.extract(f.read_bytes()))
        except Exception:
            logger.exception("survey extract failed for %s", f)
    return out


def _bucket(c: Candidate, hours: int) -> str:
    return f"{c.captured_at:%m-%d} {(c.captured_at.hour // hours) * hours:02d}h"


def gallery_context(source: Source, candidates: list[Candidate]) -> dict:
    """Pick a layout per source and shape the candidates for it.

    sequence: rovers; sol -> sequence id -> frames (a filter set or panorama tiles side by side).
    timegrid: rows = instrument, columns = time buckets (a flipbook of the day/week).
    groups: everything else; instrument -> newest frames.
    """
    candidates = sorted(candidates, key=lambda c: c.captured_at, reverse=True)
    if source.subject == "Mars" and any(c.meta.get("sequence") for c in candidates):
        sols: dict[int, dict[str, list[Candidate]]] = defaultdict(lambda: defaultdict(list))
        for c in candidates:
            sols[c.meta.get("sol", 0)][c.meta.get("sequence") or c.instrument].append(c)
        for seqs in sols.values():
            for frames in seqs.values():
                frames.sort(key=lambda c: c.captured_at)
        return {"layout": "sequence", "sols": dict(sorted(sols.items(), reverse=True))}
    if source.name == "sdo":
        hours = 3 if len({c.captured_at.date() for c in candidates}) == 1 else 6
        columns = sorted({_bucket(c, hours) for c in candidates})
        rows: dict[str, dict[str, Candidate]] = defaultdict(dict)
        for c in candidates:
            rows[c.instrument].setdefault(_bucket(c, hours), c)
        return {"layout": "timegrid", "columns": columns, "rows": dict(sorted(rows.items()))}
    by_instrument: dict[str, list[Candidate]] = defaultdict(list)
    for c in candidates:
        by_instrument[c.instrument].append(c)
    return {"layout": "groups", "groups": {k: v[:60] for k, v in sorted(by_instrument.items())}}


RENDER_ON_VIEW = {"helioviewer"}  # image URLs are server-side renders; galleries must not hit them on every page view


def localize_previews(source: Source, candidates: list[Candidate]) -> dict[str, str]:
    """For render-on-view sources, copy cached previews under site/debug/img/ and return key -> relative src."""
    if source.name not in RENDER_ON_VIEW:
        return {}
    out_dir = DEBUG_DIR / "img" / source.name
    out_dir.mkdir(parents=True, exist_ok=True)
    local = {}
    for c in candidates:
        cached = image_cache_path(str(c.preview_url))
        if cached.exists():
            dest = out_dir / f"{safe_name(c.source_id)}{cached.suffix}"
            if not dest.exists():
                dest.write_bytes(cached.read_bytes())
            local[c.key] = f"img/{source.name}/{dest.name}"
    return local


def write_debug_galleries(sources: list[Source], include_survey: bool = True) -> list[Path]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for source in sources:
        by_key = {c.key: c for c in (survey_candidates(source) if include_survey else [])}
        by_key.update({c.key: c for c in read_candidates(source.name, days=30)})
        candidates = list(by_key.values())
        local = localize_previews(source, candidates)
        if source.name in RENDER_ON_VIEW:
            candidates = [c for c in candidates if c.key in local]  # never link a render URL from a gallery
        context = gallery_context(source, candidates)
        context["local"] = local
        path = DEBUG_DIR / f"{source.name}.html"
        path.write_text(env.get_template("gallery.html.j2").render(source=source, n=len(by_key), **context))
        paths.append(path)
    by_subject: dict[str, list[str]] = defaultdict(list)
    for source in sources:
        by_subject[source.subject].append(source.name)
    index = DEBUG_DIR / "index.html"
    index.write_text(env.get_template("debug_index.html.j2").render(by_subject=dict(sorted(by_subject.items()))))
    paths.append(index)
    return paths
