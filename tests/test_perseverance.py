from datetime import UTC

from spacepics.sources.perseverance import PerseveranceSource


def test_extract_maps_full_frames_to_candidates(fixture_bytes):
    candidates = PerseveranceSource().extract(fixture_bytes("perseverance_feed.json"))
    assert candidates, "fixture should yield candidates"
    for c in candidates:
        assert c.source == "perseverance"
        assert c.captured_at.tzinfo is UTC
        assert str(c.image_url).endswith("_1200.jpg")
        assert str(c.preview_url).endswith("_800.jpg")
        assert "sol" in c.meta


def test_extract_drops_thumbnails(fixture_bytes):
    raw = fixture_bytes("perseverance_feed.json")
    assert b"Thumbnail" in raw, "fixture should include a thumbnail to prove filtering"
    candidates = PerseveranceSource().extract(raw)
    assert len(candidates) == 5
