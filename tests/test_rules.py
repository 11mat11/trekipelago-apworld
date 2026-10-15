import pytest

from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.trekipelago import TrekipelagoWorld


@pytest.mark.parametrize("kind", ["distance", "orbs"])
def test_checks_unlock_with_progression(kind):
    multiworld = setup_multiworld(TrekipelagoWorld, seed=0)
    state = CollectionState(multiworld)
    names = ([f"{i * 500}m" for i in range(1, 11)] if kind == "distance"
             else [f"Orb Check {i}" for i in range(1, 11)])
    checks = [multiworld.get_location(name, 1) for name in names]
    assert [loc.can_reach(state) for loc in checks] == [True] + [False] * 9
    progression_order = [
        "Background Tracking", "Progressive Speed", "Passive Collector",
        "Progressive Speed", "Progressive Speed", "Passive Collector",
        "Progressive Speed", "Progressive Speed", "Passive Collector",
    ]
    remaining = list(multiworld.itempool)
    for reachable, name in enumerate(progression_order, start=2):
        item = next(item for item in remaining if item.name == name)
        remaining.remove(item)
        state.collect(item, True)
        assert [loc.can_reach(state) for loc in checks] == [True] * reachable + [False] * (10 - reachable)


@pytest.mark.parametrize("names", [
    ("500m", "2500m", "5000m"),
    ("Orb Check 1", "Orb Check 5", "Orb Check 10"),
], ids=["distance", "orbs"])
def test_self_lock_rules_preserve_valid_placements(names):
    multiworld = setup_multiworld([TrekipelagoWorld] * 2, seed=0)
    early, middle, final = [multiworld.get_location(name, 1) for name in names]
    for item in multiworld.itempool:
        if item.advancement:
            assert early.item_rule(item)
            assert not final.item_rule(item)
            assert middle.item_rule(item) == (item.name != "Background Tracking")


@pytest.mark.parametrize("name", ["5000m", "Orb Check 10"])
def test_other_players_progression_does_not_unlock_checks(name):
    multiworld = setup_multiworld([TrekipelagoWorld] * 2, seed=0)
    state = CollectionState(multiworld)
    for item in multiworld.itempool:
        if item.player == 2 and item.advancement:
            state.collect(item, True)
    assert multiworld.get_location(name, 2).can_reach(state)
    assert not multiworld.get_location(name, 1).can_reach(state)
    for item in multiworld.itempool:
        if item.player == 1 and item.advancement:
            state.collect(item, True)
    assert multiworld.get_location(name, 1).can_reach(state)


@pytest.mark.parametrize("name", ["2500m", "Orb Check 5"])
def test_existing_item_rules_are_preserved(name):
    multiworld = setup_multiworld([TrekipelagoWorld] * 2, seed=0)
    location = multiworld.get_location(name, 1)
    location.item_rule = lambda item: item.name != "Passive Collector"
    multiworld.worlds[1].set_rules()
    items = {(item.player, item.name): item for item in multiworld.itempool}
    assert not location.item_rule(items[2, "Passive Collector"])
    assert location.item_rule(items[2, "Progressive Speed"])
    assert not location.item_rule(items[1, "Background Tracking"])


@pytest.mark.parametrize("goal,options,distance_reachable,orb_reachable,complete", [
    (0, {"total_distance": 1, "distance_interval": 1000, "max_orbs": 50, "orbs_per_reward": 1}, True, False, True),
    (1, {"total_distance": 1, "distance_interval": 1000, "max_orbs": 50, "orbs_per_reward": 1}, True, False, False),
    (0, {"max_orbs": 43, "orbs_per_reward": 100}, False, True, False),
    (1, {"max_orbs": 43, "orbs_per_reward": 100}, False, True, False),
    (1, {"max_orbs": 0}, False, None, False),
], ids=["distance-only", "orbs-required", "distance-required", "both-required", "orbs-disabled"])
def test_completion_requires_the_selected_objectives(goal, options, distance_reachable, orb_reachable, complete):
    multiworld = setup_multiworld(TrekipelagoWorld, seed=0, options={**options, "goal": goal})
    opts = multiworld.worlds[1].get_snapped_options()
    state = CollectionState(multiworld)
    assert multiworld.get_location(f"{opts['distances'][-1]}m", 1).can_reach(state) == distance_reachable
    if orb_reachable is not None:
        assert multiworld.get_location(f"Orb Check {opts['num_orb_locs']}", 1).can_reach(state) == orb_reachable
    assert multiworld.completion_condition[1](state) == complete
    for item in multiworld.itempool:
        if item.advancement:
            state.collect(item, True)
    assert multiworld.completion_condition[1](state)
