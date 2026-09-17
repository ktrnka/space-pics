from datetime import UTC, datetime

from spacepics.sources.apod import ApodSource


def test_extract_maps_image_to_candidate(fixture_bytes):
    candidates = ApodSource().extract(fixture_bytes("apod_feed.json"))
    assert len(candidates) == 1
    c = candidates[0]
    assert c.source == "apod"
    assert c.source_id == "2026-09-17"
    assert c.instrument == "apod"
    assert c.captured_at == datetime(2026, 9, 17, tzinfo=UTC)
    # standard-size url for both; hdurl can be a multi-MB original and only goes in meta
    assert str(c.image_url) == "https://apod.nasa.gov/apod/image/2609/JWST_Treasure_Chest_800.jpg"
    assert str(c.preview_url) == "https://apod.nasa.gov/apod/image/2609/JWST_Treasure_Chest_800.jpg"
    assert c.meta["hdurl"] == "https://apod.nasa.gov/apod/image/2609/JWST_Treasure_Chest.jpg"
    assert c.title == "A Treasure Chest in the Carina Nebula"
    # collapsed to one line, whitespace-normalised
    assert "\n" not in c.credit
    assert c.credit.startswith("ESA/Webb, NASA & CSA, M. Reiter")
    assert str(c.source_page_url) == "https://apod.nasa.gov/apod/ap260917.html"
    assert "explanation" in c.meta


def test_extract_video_returns_no_candidates(fixture_bytes):
    candidates = ApodSource().extract(fixture_bytes("apod_video.json"))
    assert candidates == []
