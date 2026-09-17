from datetime import UTC, datetime

from spacepics.sources.sdo import SdoSource


def _by_key(candidates, source_id):
    return next(c for c in candidates if c.source_id == source_id)


def test_candidate_fields_and_url_shapes(fixture_bytes):
    candidates = SdoSource().extract(fixture_bytes("sdo_listing.html"))

    aia = _by_key(candidates, "20260917_000622_1024_0171")
    assert aia.source == "sdo"
    assert aia.instrument == "0171"
    assert aia.captured_at == datetime(2026, 9, 17, 0, 6, 22, tzinfo=UTC)
    assert str(aia.image_url) == "https://sdo.gsfc.nasa.gov/assets/img/browse/2026/09/17/20260917_000622_2048_0171.jpg"
    assert str(aia.preview_url) == "https://sdo.gsfc.nasa.gov/assets/img/browse/2026/09/17/20260917_000622_1024_0171.jpg"
    assert aia.title == "SDO AIA 171 Å"
    assert aia.credit == "NASA/SDO and the AIA, EVE, and HMI science teams"
    assert str(aia.source_page_url) == "https://sdo.gsfc.nasa.gov/data/"
    assert aia.meta == {"channel": "0171", "size": 1024, "wavelength_angstrom": 171}

    hmi = _by_key(candidates, "20260917_000000_1024_HMIIC")
    assert hmi.instrument == "HMIIC"
    assert hmi.title == "SDO HMI intensitygram"
    assert hmi.meta["wavelength_angstrom"] is None


def test_subsampling_picks_first_frame_at_or_after_each_mark(fixture_bytes):
    candidates = SdoSource().extract(fixture_bytes("sdo_listing.html"))
    aia = sorted((c for c in candidates if c.instrument == "0171"), key=lambda c: c.captured_at)

    # The fixture has two 0171 frames in the 00:00-03:00 bucket (000622, 002734); the earlier wins.
    # It has two frames in the 03:00-06:00 bucket (030734, 031146); 030734 is first at/after the 03:00 mark.
    assert [c.source_id for c in aia] == [
        "20260917_000622_1024_0171",
        "20260917_030734_1024_0171",
        "20260917_060634_1024_0171",
        "20260917_090634_1024_0171",
        "20260917_120722_1024_0171",
        "20260917_150634_1024_0171",
    ]
    # 173710 falls in the same 15:00-18:00 bucket as 150634 and is dropped in favor of the earlier frame.
    assert "20260917_173710_1024_0171" not in [c.source_id for c in candidates]


def test_channels_outside_channels_list_are_dropped(fixture_bytes):
    candidates = SdoSource().extract(fixture_bytes("sdo_listing.html"))
    instruments = {c.instrument for c in candidates}

    assert "HMID" not in instruments
    assert instruments == {"0171", "HMIIC"}
    assert len(candidates) == 12
