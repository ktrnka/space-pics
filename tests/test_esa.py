from datetime import UTC

from spacepics.sources.esa import EsaSource


def _webb():
    return EsaSource("esa_webb", "https://esawebb.org", "potm")


def test_extract_maps_fields_and_picks_screen_urls(fixture_bytes):
    candidates = _webb().extract(fixture_bytes("esa_webb_feed.json"))
    assert len(candidates) == 3  # 3 list entries in the fixture, all with an image
    by_id = {c.source_id: c for c in candidates}

    c = by_id["potm2608a"]
    assert c.source == "esa_webb"
    assert c.instrument == "webb"
    assert c.captured_at.tzinfo is UTC
    assert str(c.image_url) == "https://cdn.esawebb.org/archives/images/screen/potm2608a.jpg"
    assert str(c.preview_url) == "https://cdn.esawebb.org/archives/images/screen640/potm2608a.jpg"
    assert c.title == "Striking star clusters and irregular clumps"
    assert str(c.source_page_url) == "https://esawebb.org/images/potm2608a/"
    assert c.meta["release_id"] == "potm2608"


def test_extract_fills_meta_from_detail_and_none_without_it(fixture_bytes):
    candidates = _webb().extract(fixture_bytes("esa_webb_feed.json"))
    by_id = {c.source_id: c for c in candidates}

    # potm2608a and potm2607a have per-image detail JSON in the fixture.
    with_detail = by_id["potm2608a"]
    assert with_detail.meta["ra"] == 156.27230439807377
    assert with_detail.meta["dec"] == 17.164295033283768
    assert with_detail.meta["fov"] is not None
    assert with_detail.meta["fov"]["width_arcmin"] > 0
    assert with_detail.meta["constellation"] == "Leo"
    assert with_detail.credit == "ESA/Webb, NASA & CSA, A. Leroy"

    # potm2605a has no detail record in the fixture (only the newest few are fetched).
    without_detail = by_id["potm2605a"]
    assert without_detail.meta["ra"] is None
    assert without_detail.meta["dec"] is None
    assert without_detail.meta["fov"] is None
    assert without_detail.meta["constellation"] is None
    assert without_detail.credit == "ESA/Webb, NASA & CSA"


def test_instrument_differs_by_source_name(fixture_bytes):
    raw = fixture_bytes("esa_webb_feed.json")
    webb_candidates = EsaSource("esa_webb", "https://esawebb.org", "potm").extract(raw)
    hubble_candidates = EsaSource("esa_hubble", "https://esahubble.org", "potm").extract(raw)

    assert {c.instrument for c in webb_candidates} == {"webb"}
    assert {c.instrument for c in hubble_candidates} == {"hubble"}

    # default credit fallback (no per-image detail, so nothing overrides it) differs by instrument
    webb_no_detail = next(c for c in webb_candidates if c.source_id == "potm2605a")
    hubble_no_detail = next(c for c in hubble_candidates if c.source_id == "potm2605a")
    assert webb_no_detail.credit == "ESA/Webb, NASA & CSA"
    assert hubble_no_detail.credit == "ESA/Hubble & NASA"
