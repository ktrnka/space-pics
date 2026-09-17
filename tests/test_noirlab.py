from datetime import UTC

from spacepics.sources.noirlab import NoirlabSource


def test_extract_uses_enclosure_and_pubdate(fixture_bytes):
    candidates = NoirlabSource().extract(fixture_bytes("noirlab_feed.xml"))
    assert len(candidates) == 3
    c = candidates[0]
    assert c.source_id == "iotw2637a"
    assert str(c.image_url).endswith("/screen/iotw2637a.jpg")
    assert c.captured_at.tzinfo is UTC
    assert c.title and c.meta["description"]
