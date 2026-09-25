from datetime import date

from PIL import Image

from spacepics.digest import Digest, Panel, used_wigglegram_keys
from spacepics.pipeline import is_greyscale
from spacepics.sources.perseverance import PerseveranceSource


def test_is_greyscale_tells_grey_from_colour(tmp_path):
    grey, colour = tmp_path / "grey.jpg", tmp_path / "colour.jpg"
    Image.new("RGB", (64, 64), (120, 120, 120)).save(grey)
    Image.new("RGB", (64, 64), (180, 110, 70)).save(colour)  # Mars-ish orange
    assert is_greyscale(grey)
    assert not is_greyscale(colour)


def test_used_wigglegram_keys_ignores_same_day_and_plain_panels(fixture_bytes):
    left, right, plain = PerseveranceSource().extract(fixture_bytes("perseverance_feed.json"))[:3]

    def digest(day, panels):
        return Digest(day=day, subject="Mars", title="t", intro="i", panels=panels)

    wiggle = Panel(
        candidate=left, site_image="x.gif", heading="h", blurb="b", derived_image="derived/d/wiggle-p.gif", derived_from=[left.key, right.key]
    )
    other = Panel(candidate=plain, site_image="y.jpg", heading="h", blurb="b")
    history = [digest(date(2026, 9, 20), [other, wiggle]), digest(date(2026, 9, 23), [other])]
    assert used_wigglegram_keys(history, date(2026, 9, 26)) == {left.key, right.key}
    assert used_wigglegram_keys(history, date(2026, 9, 20)) == set()  # rebuilding that day may reuse its own pair
