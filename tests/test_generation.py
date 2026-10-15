import unittest
from collections import Counter
from copy import deepcopy

from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.generic.Rules import locality_rules
from worlds.trekipelago import TrekipelagoWorld

from .cases import GENERATION_CASES
from .helpers import fill_multiworld, collect_spheres


def assert_generation(case):
    multiworld = setup_multiworld(
        [TrekipelagoWorld] * case.players, seed=case.seed, options=deepcopy(case.options),
    )
    locality_rules(multiworld)
    initial_state = CollectionState(multiworld)
    item_counts = Counter(item.player for item in multiworld.itempool)
    for player in multiworld.player_ids:
        locations = multiworld.get_locations(player)
        assert len(locations) == item_counts[player] >= 15
        assert any(loc.can_reach(initial_state) for loc in locations)

    fill_multiworld(multiworld)
    assert not multiworld.get_unfilled_locations()
    sphere_by_location, final_state = collect_spheres(multiworld)
    assert multiworld.has_beaten_game(final_state)
    tracking = [loc for loc in sphere_by_location if loc.item.name == "Background Tracking"]
    assert len(tracking) == case.players
    assert {loc.item.player for loc in tracking} == set(multiworld.player_ids)
    for location in tracking:
        assert sphere_by_location[location] == 0
        if "Background Tracking" in case.options.get("non_local_items", set()):
            assert location.player != location.item.player

    for player in multiworld.player_ids:
        opts = multiworld.worlds[player].get_snapped_options()
        for names in (
            [f"{distance}m" for distance in opts["distances"]],
            [f"Orb Check {i}" for i in range(1, opts["num_orb_locs"] + 1)],
        ):
            spheres = [sphere_by_location[multiworld.get_location(name, player)] for name in names]
            assert spheres == sorted(spheres)
            if len(spheres) > 1:
                assert spheres[-1] > spheres[0]


class TestGeneration(unittest.TestCase):
    def test_seed_matrix(self):
        for case in GENERATION_CASES:
            with self.subTest(case=case.id, options=case.options):
                assert_generation(case)
