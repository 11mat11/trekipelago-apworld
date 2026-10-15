import zipfile
import zlib
from argparse import Namespace
from collections import Counter

import pytest
from BaseClasses import (
    CollectionState,
    ItemClassification,
    LocationProgressType,
    PlandoOptions,
)
from Main import main
from test.general import setup_multiworld
from Utils import output_path, restricted_loads
from worlds.trekipelago import TrekipelagoWorld
from worlds.trekipelago.items import item_dictionary


def generate_with_common_options(options, *, output_directory=None, seed=0):
    """Use Main so core applies inventory, locality, location options, and balancing."""
    if isinstance(options, dict):
        options = [options]
    players = range(1, len(options) + 1)
    args = Namespace(
        multi=len(options),
        race=False,
        outputname=f"common-options-{seed}",
        outputpath=str(output_directory) if output_directory else None,
        plando=PlandoOptions.items,
        game={player: "Trekipelago" for player in players},
        name={player: f"Tester{player}" for player in players},
        sprite={},
        sprite_pool={},
        csv_output=False,
        skip_output=output_directory is None,
        spoiler_only=False,
        skip_prog_balancing=False,
        spoiler=0,
    )
    for name, option_type in TrekipelagoWorld.options_dataclass.type_hints.items():
        values = {}
        for player, overrides in enumerate(options, start=1):
            option = option_type.from_any(overrides.get(name, option_type.default))
            option.verify(TrekipelagoWorld, args.name[player], args.plando)
            values[player] = option
        setattr(args, name, values)
    return main(args, seed=seed, baked_server_options={"hint_cost": 10})


def test_create_item_supports_every_catalog_entry():
    world = setup_multiworld(TrekipelagoWorld, steps=(), seed=0).worlds[1]
    for name, data in item_dictionary.items():
        item = world.create_item(name)
        assert (item.name, item.code, item.classification, item.player) == (
            name,
            data["id"],
            data["classification"],
            1,
        )
    with pytest.raises(KeyError):
        world.create_item("Burst Orbs")


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
    # The world actively caps core progression items (Background Tracking, Passive Collector, Progressive Speed)
    # so that extra copies are not placed into the world when given in start inventory.
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
    # 5 total allowed. 3 given via start inventories (1 from start_inventory, 2 from pool).
    # Since start_inventory caps progression items to avoid undefined app behavior,
    # exactly 2 remain in the world.
    assert placed["Progressive Speed"] == 2
    assert placed["Background Tracking"] == 0
    assert multiworld.can_beat_game()


@pytest.mark.parametrize("seed", range(3))
def test_locality_exclusions_and_priority_work_with_starting_items(seed):
    options = {
        "start_inventory_from_pool": {"Background Tracking": 1},
        "local_items": {"Passive Collector"},
        "non_local_items": {"Progressive Speed"},
        "exclude_locations": {"5000m"},
        "priority_locations": {"500m"},
        "accessibility": "full",
        "progression_balancing": "normal",
    }
    multiworld = generate_with_common_options(
        [options.copy(), options.copy()], seed=seed
    )
    for player in multiworld.player_ids:
        excluded = multiworld.get_location("5000m", player)
        assert excluded.progress_type == LocationProgressType.EXCLUDED
        assert not (excluded.item.advancement or excluded.item.useful)
        priority = multiworld.get_location("500m", player)
        assert priority.progress_type == LocationProgressType.PRIORITY
        assert priority.item.advancement
    for location in multiworld.get_filled_locations():
        if location.item.name == "Passive Collector":
            assert location.player == location.item.player
        if location.item.name == "Progressive Speed":
            assert location.player != location.item.player
    assert multiworld.can_beat_game()


def test_starting_items_and_hints_are_exported_for_the_client(tmp_path, monkeypatch):
    monkeypatch.setattr(output_path, "cached_path", str(tmp_path), raising=False)
    multiworld = generate_with_common_options(
        {
            "start_inventory_from_pool": {"Background Tracking": 1},
            "start_hints": {"Passive Collector"},
            "start_location_hints": {"Orb Check 2"},
        },
        output_directory=tmp_path,
    )
    (archive_path,) = tmp_path.glob("*.zip")
    with zipfile.ZipFile(archive_path) as archive:
        (data_name,) = [
            name for name in archive.namelist() if name.endswith(".archipelago")
        ]
        encoded = archive.read(data_name)
    assert encoded[0] == 3
    data = restricted_loads(zlib.decompress(encoded[1:]))
    assert data["precollected_items"][1] == [
        TrekipelagoWorld.item_name_to_id["Background Tracking"]
    ]
    hints = data["precollected_hints"][1]
    collector_locations = {
        location.address
        for location in multiworld.get_filled_locations()
        if location.item.name == "Passive Collector"
    }
    hinted_locations = {hint.location for hint in hints}
    assert collector_locations <= hinted_locations
    assert multiworld.get_location("Orb Check 2", 1).address in hinted_locations
