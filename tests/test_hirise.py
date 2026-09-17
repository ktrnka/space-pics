from datetime import UTC

from spacepics.sources.hirise import HiriseSource


def test_extract_maps_item_to_candidate(fixture_bytes):
    candidates = HiriseSource().extract(fixture_bytes("hirise_feed.xml"))
    assert len(candidates) == 1
    c = candidates[0]
    assert c.source == "hirise"
    assert c.source_id == "ESP_065221_2055"
    assert c.instrument == "hirise"
    assert c.captured_at.tzinfo is UTC
    assert str(c.image_url) == "https://static.uahirise.org/hipod/ESP_065221_2055.jpg"
    assert c.image_url == c.preview_url
    assert c.title == "Layers in Flammarion Crater"
    assert not c.title.startswith("HiPOD")
    assert c.credit == "NASA/JPL-Caltech/University of Arizona"
    assert str(c.source_page_url) == "https://uahirise.org/hipod/ESP_065221_2055"
    assert "<" not in c.meta["description"]
    assert "layers" in c.meta["description"].lower()
