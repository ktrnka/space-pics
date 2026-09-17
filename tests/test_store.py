from datetime import UTC, date, datetime

from spacepics import store
from spacepics.models import Candidate


def cand(i: int, day: str) -> Candidate:
    return Candidate(
        source="t",
        source_id=str(i),
        instrument="x",
        captured_at=datetime(2026, 9, 17, tzinfo=UTC),
        image_url="https://example.org/a.jpg",
        preview_url="https://example.org/a.jpg",
        title=day,
        credit="c",
    )


def test_rolling_window_dedupes_by_key_newest_wins(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "CANDIDATES_DIR", tmp_path)
    store.write_candidates("t", date(2026, 9, 15), [cand(1, "d15"), cand(2, "d15")])
    store.write_candidates("t", date(2026, 9, 16), [cand(2, "d16"), cand(3, "d16")])
    latest = store.read_candidates("t")
    assert sorted(c.source_id for c in latest) == ["2", "3"]
    window = store.read_candidates("t", days=2)
    assert sorted(c.source_id for c in window) == ["1", "2", "3"]
    assert next(c for c in window if c.source_id == "2").title == "d16"
