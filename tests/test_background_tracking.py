import unittest

from BaseClasses import CollectionState
from Fill import FillError, distribute_early_items
from test.general import setup_multiworld
from worlds.trekipelago import TrekipelagoWorld


class TestBackgroundTrackingSphereZero(unittest.TestCase):
    def test_early_placement_with_minimum_distance_checks(self):
        for players in (1, 4):
            for seed in range(10):
                with self.subTest(players=players, seed=seed):
                    multiworld = setup_multiworld(
                        [TrekipelagoWorld] * players, seed=seed,
                        options={"total_distance": 1, "distance_interval": 1000, "max_orbs": 0},
                    )
                    locations = list(multiworld.get_unfilled_locations())
                    items = list(multiworld.itempool)
                    multiworld.random.shuffle(locations)
                    multiworld.random.shuffle(items)
                    distribute_early_items(multiworld, locations, items)
                    state = CollectionState(multiworld)
                    tracking = [loc for loc in multiworld.get_filled_locations()
                                if loc.item.name == "Background Tracking"]
                    self.assertEqual(len(tracking), players)
                    self.assertTrue(all(loc.can_reach(state) for loc in tracking))
                    self.assertTrue(all(loc.locked for loc in tracking))


    def test_late_foreign_placement_is_rejected(self):
        multiworld = setup_multiworld([TrekipelagoWorld] * 2, seed=0)
        item = next(item for item in multiworld.itempool
                    if item.name == "Background Tracking" and item.player == 1)
        location = multiworld.get_location("5000m", 2)
        self.assertFalse(location.item_rule(item))
        self.assertFalse(location.can_reach(CollectionState(multiworld)))
        # Direct placement bypasses item_rule; final validation must still catch it.
        location.place_locked_item(item)
        multiworld.itempool.remove(item)
        with self.assertRaisesRegex(FillError, "Background Tracking must be available in sphere 0"):
            multiworld.worlds[1].finalize_multiworld()

    def test_missing_placement_is_rejected(self):
        multiworld = setup_multiworld(TrekipelagoWorld, seed=0)
        with self.assertRaisesRegex(FillError, "not placed"):
            multiworld.worlds[1].finalize_multiworld()

    def test_starting_inventory_satisfies_requirement(self):
        multiworld = setup_multiworld(TrekipelagoWorld, seed=0)
        item = next(item for item in multiworld.itempool if item.name == "Background Tracking")
        multiworld.itempool.remove(item)
        multiworld.push_precollected(item)
        multiworld.worlds[1].finalize_multiworld()
