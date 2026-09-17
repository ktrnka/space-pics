from datetime import UTC, datetime

import yaml

from spacepics import reference
from spacepics.models import Candidate


def test_card_lookup_and_readable_meta(tmp_path, monkeypatch):
    monkeypatch.setattr(reference, "CARDS_DIR", tmp_path)
    reference.load_cards.cache_clear()
    (tmp_path / "x.yaml").write_text(
        yaml.safe_dump(
            [
                {
                    "spacecraft": "Perseverance",
                    "instruments": ["MCZ_LEFT", "MCZ_RIGHT"],
                    "name": "Mastcam-Z",
                    "what_it_is": "A zoomable camera.",
                    "meta_labels": {"filter_name": "Filter wheel position"},
                }
            ]
        )
    )
    c = Candidate(
        source="perseverance",
        source_id="a",
        spacecraft="Perseverance",
        instrument="MCZ_RIGHT",
        captured_at=datetime(2026, 9, 17, 5, tzinfo=UTC),
        image_url="https://example.org/a.jpg",
        preview_url="https://example.org/a.jpg",
        title="t",
        credit="c",
        meta={"sol": 1982, "filter_name": "ZCAM_R2_866NM", "product": None, "fov": {"width_arcmin": 3.5}},
    )
    card = reference.card_for(c)
    assert card and card.name == "Mastcam-Z"
    lines = dict(reference.readable_meta(c, card))
    assert lines["Captured"] == "2026-09-17 05:00 UTC"
    assert lines["Filter wheel position"] == "ZCAM_R2_866NM"
    assert "Product type" not in lines  # None values are skipped
    assert lines["Field of view (arcmin)"] == "width arcmin 3.5"
    reference.load_cards.cache_clear()
