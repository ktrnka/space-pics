import random
from datetime import UTC, datetime

from spacepics.models import Candidate
from spacepics.pipeline import stratified_choice


def cand(source: str, instrument: str, i: int) -> Candidate:
    return Candidate(
        source=source,
        source_id=f"{instrument}-{i}",
        instrument=instrument,
        captured_at=datetime(2026, 9, 17, tzinfo=UTC),
        image_url="https://example.org/a.jpg",
        preview_url="https://example.org/a.jpg",
        title="t",
        credit="c",
    )


def test_instruments_drawn_uniformly_within_source():
    pools = {"perseverance": [cand("perseverance", "HAZCAM", i) for i in range(50)] + [cand("perseverance", "MCZ", 0)]}
    picks = [stratified_choice(pools, {}, random.Random(seed)).instrument for seed in range(200)]
    assert 0.3 < picks.count("MCZ") / len(picks) < 0.7


def test_avoids_yesterdays_source_when_possible():
    pools = {"sdo": [cand("sdo", "0171", 0)], "epic": [cand("epic", "epic", 0)]}
    assert all(stratified_choice(pools, {}, random.Random(s), avoid_source="sdo").source == "epic" for s in range(20))
    assert stratified_choice({"sdo": pools["sdo"]}, {}, random.Random(1), avoid_source="sdo").source == "sdo"


def test_empty_pools_are_skipped():
    pools = {"apod": [], "hirise": [cand("hirise", "hirise", 0)]}
    assert stratified_choice(pools, {}, random.Random(0)).source == "hirise"


def test_source_weights_bias_the_draw():
    pools = {"a": [cand("a", "x", 0)], "b": [cand("b", "x", 0)]}
    picks = [stratified_choice(pools, {"a": 9, "b": 1}, random.Random(s)).source for s in range(300)]
    assert picks.count("a") > 240
