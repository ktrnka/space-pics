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


def test_fetch_merges_pages_and_drops_repeats(fixture_bytes, monkeypatch):
    import json

    import httpx

    from spacepics.sources import perseverance

    monkeypatch.setattr(perseverance, "PAGE_PAUSE_S", 0)
    page0 = json.loads(fixture_bytes("perseverance_feed.json"))
    n = len(page0["images"])
    # page 1 repeats one frame from page 0 (the feed shifted) and is short, so paging stops there
    page1 = {**page0, "images": [page0["images"][0]] + [{**img, "imageid": img["imageid"] + "_p1"} for img in page0["images"][1:-1]]}
    pages = {"0": page0, "1": page1}
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.params["page"])
        return httpx.Response(200, json=pages[request.url.params["page"]])

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        merged = json.loads(PerseveranceSource(num=n + 1, pages=4).fetch_feed(client))
    assert requested == ["0"], "a short page 0 means there is nothing further to fetch"

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        merged = json.loads(PerseveranceSource(num=n, pages=4).fetch_feed(client))
    assert requested[1:] == ["0", "1"]
    assert merged["pages_fetched"] == 2
    assert len(merged["images"]) == 2 * n - 2
    assert len(PerseveranceSource().extract(json.dumps(merged).encode())) > 5
