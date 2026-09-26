import unittest

from test.general import setup_multiworld
from worlds.trekipelago import TrekipelagoWorld
from worlds.trekipelago.locations import location_name_to_id, TREKIPELAGO_LOCATION_BASE_ID

from .helpers import fill_multiworld


class TestMinimumLocations(unittest.TestCase):
    def test_short_distance_fallback_boundary(self):
        for orb_checks, expected_interval in ((0, 50), (4, 50), (5, 100)):
            with self.subTest(orb_checks=orb_checks):
                multiworld = setup_multiworld(TrekipelagoWorld, seed=0, options={
                    "total_distance": 1, "distance_interval": 1000,
                    "max_orbs": orb_checks, "orbs_per_reward": 1,
                })
                world = multiworld.worlds[1]
                opts = world.get_snapped_options()
                self.assertEqual(opts["interval"], expected_interval)
                self.assertEqual(opts["total_dist"], 1000)
                self.assertEqual(opts["max_orbs"], orb_checks)
                self.assertGreaterEqual(len(multiworld.get_locations(1)), 15)
                self.assertEqual(world.fill_slot_data()["distance_step"], expected_interval)
                for location_id, meters in world.fill_slot_data()["distance_checks"]:
                    self.assertEqual(multiworld.get_location(f"{meters}m", 1).address, location_id)

    def test_supplemental_ids_preserve_existing_mappings(self):
        for distance in range(100, 500001, 100):
            self.assertEqual(location_name_to_id[f"{distance}m"],
                             TREKIPELAGO_LOCATION_BASE_ID + distance // 100)
        for index in range(1, 101):
            self.assertEqual(location_name_to_id[f"Orb Check {index}"],
                             TREKIPELAGO_LOCATION_BASE_ID + 5000 + index)
        self.assertEqual(len(location_name_to_id), len(set(location_name_to_id.values())))
        for distance in range(50, 1000, 100):
            self.assertIn(f"{distance}m", location_name_to_id)

    def test_exactly_fifteen_locations_preserve_requested_interval(self):
        multiworld = setup_multiworld(TrekipelagoWorld, seed=0, options={
            "total_distance": 5, "distance_interval": 500,
            "max_orbs": 5, "orbs_per_reward": 1,
        })
        opts = multiworld.worlds[1].get_snapped_options()
        self.assertEqual(opts["interval"], 500)
        self.assertEqual(opts["num_dist_locs"] + opts["num_orb_locs"], 15)
        self.assertEqual(len(multiworld.itempool), 15)

    def test_fourteen_locations_trigger_fallback(self):
        multiworld = setup_multiworld(TrekipelagoWorld, seed=0, options={
            "total_distance": 5, "distance_interval": 500,
            "max_orbs": 4, "orbs_per_reward": 1,
        })
        world = multiworld.worlds[1]
        opts = world.get_snapped_options()
        self.assertLess(opts["interval"], 500)
        self.assertGreaterEqual(opts["num_dist_locs"] + opts["num_orb_locs"], 15)
        self.assertEqual(opts["distances"][-1], 5000)
        self.assertEqual(opts["orbs"], [1, 2, 3, 4])
        self.assertEqual(len(multiworld.itempool), len(multiworld.get_locations(1)))
        slot = world.fill_slot_data()
        self.assertEqual(len(slot["distance_checks"]) + len(slot["orb_checks"]),
                         len(multiworld.itempool))

    def test_generation_without_orbs(self):
        # Includes seeds that failed in the old ten-location configuration.
        for players in (1, 4):
            for km, interval in ((1, 1000), (2, 1000), (3, 200), (5, 500)):
                for seed in range(100):
                    with self.subTest(players=players, km=km, interval=interval, seed=seed):
                        multiworld = setup_multiworld(
                            [TrekipelagoWorld] * players, seed=seed,
                            options={"total_distance": km, "distance_interval": interval, "max_orbs": 0},
                        )
                        for player in multiworld.player_ids:
                            self.assertGreaterEqual(len(multiworld.get_locations(player)), 15)
                        fill_multiworld(multiworld)
                        self.assertTrue(multiworld.can_beat_game())
                        self.assertFalse(multiworld.get_unfilled_locations())
