import unittest

from BaseClasses import CollectionState
from test.general import setup_multiworld
from worlds.trekipelago import TrekipelagoWorld

from .helpers import fill_multiworld


class TestOrbPacing(unittest.TestCase):
    def test_orb_checks_unlock_with_progression(self):
        multiworld = setup_multiworld(TrekipelagoWorld, seed=0)
        state = CollectionState(multiworld)
        checks = [multiworld.get_location(f"Orb Check {i}", 1) for i in range(1, 11)]
        self.assertEqual([loc.can_reach(state) for loc in checks], [True] + [False] * 9)
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
            self.assertEqual([loc.can_reach(state) for loc in checks],
                             [True] * reachable + [False] * (10 - reachable))

    def test_self_lock_protection_is_player_specific(self):
        multiworld = setup_multiworld([TrekipelagoWorld] * 2, seed=0)
        final_check = multiworld.get_location("Orb Check 10", 1)
        early_check = multiworld.get_location("Orb Check 1", 1)
        for item in multiworld.itempool:
            if item.name in {"Background Tracking", "Progressive Speed", "Passive Collector"}:
                self.assertEqual(final_check.item_rule(item), item.player != 1)
                self.assertTrue(early_check.item_rule(item))

    def test_existing_item_rules_are_preserved(self):
        multiworld = setup_multiworld(TrekipelagoWorld, seed=0)
        location = multiworld.get_location("Orb Check 10", 1)
        location.item_rule = lambda item: False
        multiworld.worlds[1].set_rules()
        self.assertTrue(all(not location.item_rule(item) for item in multiworld.itempool))

    def test_filled_orb_checks_span_spheres(self):
        configurations = [
            {"total_distance": 1, "distance_interval": 1000, "max_orbs": 14, "orbs_per_reward": 1},
            {"total_distance": 1, "distance_interval": 1000, "max_orbs": 5, "orbs_per_reward": 1},
            {"max_orbs": 43, "orbs_per_reward": 100},
            {"max_orbs": 50, "orbs_per_reward": 5},
            {"distance_interval": 900, "max_orbs": 943, "orbs_per_reward": 100},
            {"max_orbs": 999, "orbs_per_reward": 1},
        ]
        for players in (1, 4):
            for config in configurations:
                for seed in range(30):
                    with self.subTest(players=players, config=config, seed=seed):
                        multiworld = setup_multiworld(
                            [TrekipelagoWorld] * players, seed=seed,
                            options={**config, "goal": 1},
                        )
                        fill_multiworld(multiworld)
                        self.assertTrue(multiworld.can_beat_game())
                        self.assertFalse(multiworld.get_unfilled_locations())
                        sphere_by_location = {}
                        for index, sphere in enumerate(multiworld.get_spheres()):
                            self.assertTrue(sphere, "Generated seed has unreachable locations")
                            sphere_by_location.update((loc, index) for loc in sphere)
                        for player in multiworld.player_ids:
                            count = multiworld.worlds[player].get_snapped_options()["num_orb_locs"]
                            orb_spheres = [
                                sphere_by_location[multiworld.get_location(f"Orb Check {i}", player)]
                                for i in range(1, count + 1)
                            ]
                            self.assertEqual(orb_spheres, sorted(orb_spheres))
                            if count > 1:
                                self.assertGreater(orb_spheres[-1], orb_spheres[0])
