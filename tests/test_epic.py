from datetime import UTC, datetime

from spacepics.sources.epic import EpicSource


def test_extract_builds_image_url_from_date(fixture_bytes):
    candidates = EpicSource().extract(fixture_bytes("epic_feed.json"))
    assert candidates, "fixture should yield candidates"
    c = candidates[0]
    assert c.source_id == "20260913010436"
    expected = "https://epic.gsfc.nasa.gov/archive/natural/2026/09/13/jpg/epic_1b_20260913010436.jpg"
    assert str(c.image_url) == expected
    assert str(c.preview_url) == expected


def test_extract_maps_fields(fixture_bytes):
    candidates = EpicSource().extract(fixture_bytes("epic_feed.json"))
    c = candidates[0]
    assert c.source == "epic"
    assert c.instrument == "epic_natural"
    assert c.captured_at == datetime(2026, 9, 13, 0, 59, 48, tzinfo=UTC)
    assert c.captured_at.tzinfo is UTC
    assert c.credit == "NASA/NOAA EPIC, DSCOVR"
    assert c.source_page_url is not None and str(c.source_page_url) == "https://epic.gsfc.nasa.gov/"
    assert c.meta["centroid_lat"] == 6.965332
    assert c.meta["centroid_lon"] == 165.717773
    assert c.meta["version"] == "04"
    assert "7.0" in c.title and "165.7" in c.title
    assert len(candidates) == 3
