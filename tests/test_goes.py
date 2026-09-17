from datetime import UTC, datetime

from spacepics.sources.goes import GoesSource


def test_extract_parses_day_of_year_and_subsamples(fixture_bytes):
    candidates = GoesSource().extract(fixture_bytes("goes_listing.html"))
    assert candidates
    days = {c.captured_at.date() for c in candidates}
    assert datetime(2026, 9, 17, tzinfo=UTC).date() in days  # day 260 of 2026
    # at most one frame per 3-hour bucket per day
    buckets = [(c.captured_at.date(), c.captured_at.hour // 3) for c in candidates]
    assert len(buckets) == len(set(buckets))
    c = candidates[0]
    assert str(c.image_url).endswith("-1808x1808.jpg")
    assert str(c.preview_url).endswith("-678x678.jpg")
    assert str(c.thumbnail_url).endswith("-339x339.jpg")
    assert c.spacecraft == "GOES-19"
