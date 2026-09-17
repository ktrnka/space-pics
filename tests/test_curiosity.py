from datetime import UTC

from spacepics.sources.curiosity import CuriositySource


def test_extract_maps_full_frames_to_candidates(fixture_bytes):
    candidates = CuriositySource().extract(fixture_bytes("curiosity_feed.json"))
    assert candidates, "fixture should yield candidates"
    for c in candidates:
        assert c.source == "curiosity"
        assert c.spacecraft == "Curiosity"
        assert c.captured_at.tzinfo is UTC
        assert str(c.image_url) == str(c.preview_url), "no smaller variant on this feed; preview falls back to image_url"
        assert c.source_page_url is None, "link is feed-relative on this feed"
        assert "sol" in c.meta

    chemcam = next(c for c in candidates if c.instrument == "CHEMCAM_RMI")
    assert chemcam.title == "Curiosity CHEMCAM_RMI, sol 5017"
    assert chemcam.meta["mast_az"] == "345.621"
    assert chemcam.meta["mast_el"] == "-44.8349"
    assert chemcam.meta["lmst"] == "Sol-05017M11:12:52.533"
    assert chemcam.credit == "NASA/JPL-Caltech/LANL/CNES/CNRS/IRAP/IAS/LPG"


def test_extract_drops_thumbnails(fixture_bytes):
    raw = fixture_bytes("curiosity_feed.json")
    assert b'"is_thumbnail": true' in raw, "fixture should include a thumbnail to prove filtering"
    candidates = CuriositySource().extract(raw)
    assert len(candidates) == 3
    assert all(not c.source_id.startswith("NRB_842884851") for c in candidates)
