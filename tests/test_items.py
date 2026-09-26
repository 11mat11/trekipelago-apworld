from collections import Counter

import pytest

from BaseClasses import ItemClassification
from test.general import setup_multiworld
from worlds.trekipelago import TrekipelagoWorld
from worlds.trekipelago.items import item_dictionary


@pytest.mark.parametrize("ratio,classification", [
    (0, ItemClassification.trap), (100, ItemClassification.useful),
])
def test_filler_ratio_extremes_preserve_core_progression(ratio, classification):
    multiworld = setup_multiworld(TrekipelagoWorld, seed=0, options={"buff_ratio": ratio})
    progression = [item for item in multiworld.itempool if item.advancement]
    assert Counter(item.name for item in progression) == {
        "Background Tracking": 1, "Progressive Speed": 5, "Passive Collector": 3,
    }
    filler = [item for item in multiworld.itempool if not item.advancement]
    assert len(filler) == len(multiworld.get_locations(1)) - 9
    assert filler
    assert all(item.classification == classification for item in filler)
    assert all(item.name != "Burst Orbs" for item in multiworld.itempool)


def test_removed_buff_does_not_shift_existing_item_ids():
    expected_names = ["Background Tracking", "Passive Collector", "Progressive Speed"]
    timed_effects = [
        "Speed Boost", "Double Distance", "Double Orb Spawns", "Double Collected Orbs",
        "Trap: Slow Movement", "Trap: Half Distance", "Trap: Half Orb Spawns",
        "Trap: Half Collected Orbs",
    ]
    expected_names.extend(
        f"{effect} ({duration})"
        for effect in timed_effects
        for duration in ("5m", "15m", "30m")
    )
    expected_names.extend(["Trap: Map Blindness (1m)", "Trap: Map Blindness (3m)"])
    expected_ids = [1111, 1112, 1113, *range(1115, 1141)]
    expected_mapping = dict(zip(expected_names, expected_ids))

    assert "Burst Orbs" not in item_dictionary
    assert TrekipelagoWorld.item_name_to_id == expected_mapping
