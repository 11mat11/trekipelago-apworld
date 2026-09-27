from collections import Counter

from BaseClasses import CollectionState, MultiWorld
from Fill import balance_multiworld_progression, distribute_items_restrictive
from worlds.AutoWorld import call_all


def fill_multiworld(multiworld: MultiWorld) -> None:
    """Run fill, balancing, and final validation in the generator's order."""
    distribute_items_restrictive(multiworld)
    call_all(multiworld, "post_fill")
    if multiworld.players > 1:
        balance_multiworld_progression(multiworld)
    call_all(multiworld, "finalize_multiworld")


def assert_layout(multiworld: MultiWorld, player: int) -> None:
    """Check the public layout, item counts and exported thresholds together."""
    world = multiworld.worlds[player]
    opts = world.get_snapped_options()
    locations = multiworld.get_locations(player)
    items = [item for item in multiworld.itempool if item.player == player]
    assert len(locations) == len(items) >= 15
    progression = Counter(item.name for item in items if item.advancement)
    assert progression == {"Background Tracking": 1, "Progressive Speed": 5, "Passive Collector": 3}
    assert len(items) - sum(progression.values()) == len(locations) - 9
    assert opts["num_dist_locs"] == len(opts["distances"])
    assert opts["num_orb_locs"] == len(opts["orbs"])
    assert opts["orbs_per_reward"] == world.options.orbs_per_reward.value
    assert all(previous < current for previous, current in zip(opts["orbs"], opts["orbs"][1:]))
    assert opts["distances"][-1] == opts["total_dist"]
    assert opts["orbs"][-1:] == ([opts["max_orbs"]] if opts["max_orbs"] else [])
    slot = world.fill_slot_data()
    assert slot["distance_step"] == min(100, opts["interval"])
    assert slot["distance_checks"] == [
        [world.location_name_to_id[f"{meters}m"], meters] for meters in opts["distances"]
    ]
    assert slot["orb_checks"] == [
        [world.location_name_to_id[f"Orb Check {index}"], orbs]
        for index, orbs in enumerate(opts["orbs"], start=1)
    ]
    exported_ids = [identifier for identifier, _ in slot["distance_checks"] + slot["orb_checks"]]
    assert len(exported_ids) == len(set(exported_ids)) == len(locations)
    assert set(exported_ids) == {loc.address for loc in locations}


def collect_spheres(multiworld: MultiWorld):
    """Traverse reachability once, returning sphere numbers and the final state."""
    state = CollectionState(multiworld)
    remaining = set(multiworld.get_filled_locations())
    sphere_by_location = {}
    index = 0
    while remaining:
        sphere = {location for location in remaining if location.can_reach(state)}
        assert sphere, f"Unreachable locations: {sorted(str(loc) for loc in remaining)}"
        sphere_by_location.update((location, index) for location in sphere)
        for location in sphere:
            state.collect(location.item, True, location)
        remaining -= sphere
        index += 1
    return sphere_by_location, state
