"""JSONL persistence for candidates and picks. Kept hand-editable."""

from datetime import date
from pathlib import Path

from .models import Candidate, Pick
from .paths import CANDIDATES_DIR, PICKS_FILE


def write_candidates(source: str, day: date, candidates: list[Candidate]) -> Path:
    path = CANDIDATES_DIR / source / f"{day.isoformat()}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(c.model_dump_json() + "\n" for c in candidates))
    return path


def read_candidates(source: str, day: date | None = None, days: int = 1) -> list[Candidate]:
    """Candidates from one source: the newest `days` files (default just the latest), or one specific day.

    Feeds overlap day to day, so candidates are de-duplicated by key, newest file winning.
    """
    src_dir = CANDIDATES_DIR / source
    files = [src_dir / f"{day.isoformat()}.jsonl"] if day is not None else sorted(src_dir.glob("*.jsonl"))[-days:]
    by_key: dict[str, Candidate] = {}
    for f in files:
        if f.exists():
            for line in f.read_text().splitlines():
                if line.strip():
                    c = Candidate.model_validate_json(line)
                    by_key[c.key] = c
    return list(by_key.values())


def read_picks() -> list[Pick]:
    if not PICKS_FILE.exists():
        return []
    return [Pick.model_validate_json(line) for line in PICKS_FILE.read_text().splitlines() if line.strip()]


def upsert_pick(pick: Pick) -> None:
    """One pick per day; re-running a day replaces that day's line."""
    picks = [p for p in read_picks() if p.day != pick.day] + [pick]
    picks.sort(key=lambda p: p.day)
    PICKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PICKS_FILE.write_text("".join(p.model_dump_json() + "\n" for p in picks))
