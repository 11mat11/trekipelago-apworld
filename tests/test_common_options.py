from collections import Counter

import pytest
from BaseClasses import CollectionState, ItemClassification
from test.general import setup_default_world


# Generate with options using AP's test suite setup method
def generate_with_common_options(options, players=1, seed=0):
    multiworld = setup_default_world(
        game="Trekipelago",
        options={1: options}
        if players == 1
        else {i: options.copy() for i in range(1, players + 1)},
        seed=seed,
    )
    return multiworld


def test_create_item_supports_every_catalog_entry():
    from trekipelago.items import item_dictionary

    multiworld = generate_with_common_options({})
    world = multiworld.worlds[1]

    for name in item_dictionary.keys():
        item = world.create_item(name)
        assert item.name == name
        assert item.code == item_dictionary[name]["id"]
        assert item.classification == item_dictionary[name]["classification"]


@pytest.mark.parametrize(
    "inventory_option", ["start_inventory", "start_inventory_from_pool"]
)
@pytest.mark.parametrize("buff_ratio", [0, 100])
def test_starting_inventory_and_pool_replacements(inventory_option, buff_ratio):
    starting_items = {
        "Background Tracking": 1,
        "Passive Collector": 3,
        "Progressive Speed": 5,
    }
    multiworld = generate_with_common_options(
        {
            inventory_option: starting_items.copy(),
            "buff_ratio": buff_ratio,
        }
    )
    assert (
        Counter(item.name for item in multiworld.precollected_items[1])
        == starting_items
    )
    state = CollectionState(multiworld)
    assert all(state.has(name, 1, count) for name, count in starting_items.items())
    assert multiworld.get_location("5000m", 1).can_reach(state)
    assert not multiworld.early_items[1].get("Background Tracking", 0)

    placed_items = [location.item for location in multiworld.get_locations(1)]
    progression = Counter(item.name for item in placed_items if item.advancement)
    # The world now actively caps core progression items regardless of how they are granted.
    # Therefore, no core progression should be found on the map if the max amount was started with.
    assert progression == {}
    expected_classification = (
        ItemClassification.trap if buff_ratio == 0 else ItemClassification.useful
    )
    assert all(
        item.classification == expected_classification
        for item in placed_items
        if not item.advancement
    )
    assert len(placed_items) == len(multiworld.itempool)
    assert multiworld.can_beat_game()


def test_both_inventory_options_keep_their_distinct_semantics():
    multiworld = generate_with_common_options(
        {
            "start_inventory": {"Progressive Speed": 1, "Speed Boost (5m)": 2},
            "start_inventory_from_pool": {
                "Progressive Speed": 2,
                "Background Tracking": 1,
            },
        }
    )

    assert Counter(item.name for item in multiworld.precollected_items[1]) == {
        "Progressive Speed": 3,
        "Background Tracking": 1,
        "Speed Boost (5m)": 2,
    }

    placed = Counter(location.item.name for location in multiworld.get_locations(1))

    # 5 total allowed. 3 given through start inventories (1 from pool, 1 from standard).
    # Since start_inventory now respects hard caps, exactly 2 should be placed.
    assert placed["Progressive Speed"] == 2
    assert placed["Background Tracking"] == 0
    assert multiworld.can_beat_game()


@pytest.mark.parametrize("seed", range(3))
def test_locality_exclusions_and_priority_work_with_starting_items(seed):
    multiworld = generate_with_common_options(
        {
            "start_inventory": {"Background Tracking": 1},
            "start_inventory_from_pool": {"Progressive Speed": 2},
            "local_items": ["Passive Collector"],
            "non_local_items": ["Progressive Speed"],
            "exclude_locations": ["1000m", "2000m"],
            "priority_locations": ["Orb Check 1"],
        },
        players=2,
        seed=seed,
    )

    world1_placed = [loc.item for loc in multiworld.get_locations(1)]
    assert (
        sum(
            1
            for item in world1_placed
            if item.name == "Passive Collector" and item.player == 1
        )
        == 3
    )
    assert not any(
        item.name == "Progressive Speed" and item.player == 1 for item in world1_placed
    )

    for loc_name in ["1000m", "2000m"]:
        item = multiworld.get_location(loc_name, 1).item
        assert not item.advancement, (
            f"Excluded location {loc_name} contained progression: {item.name}"
        )

    orb1 = multiworld.get_location("Orb Check 1", 1).item
    assert orb1.advancement, (
        f"Priority location Orb Check 1 did not contain progression: {orb1.name}"
    )


def test_starting_items_and_hints_are_exported_for_the_client():
    multiworld = generate_with_common_options(
        {
            "start_inventory": {"Background Tracking": 1, "Progressive Speed": 1},
            "start_inventory_from_pool": {"Passive Collector": 1},
            "start_hints": ["Progressive Speed"],
            "start_location_hints": ["1000m"],
        }
    )

    # Starting inventory (exported normally by Archipelago, not slot_data)
    assert Counter(item.name for item in multiworld.precollected_items[1]) == {
        "Background Tracking": 1,
        "Progressive Speed": 1,
        "Passive Collector": 1,
    }
