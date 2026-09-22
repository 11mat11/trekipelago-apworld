from . import TrekipelagoTestBase


class TestTrekipelagoStandard(TrekipelagoTestBase):
    options = {
        "total_distance": 5000,
        "distance_interval": 500,
        "max_orbs": 50,
        "orbs_per_reward": 5,
        "goal": 1,  # distance_and_orbs
    }

    def test_item_generation(self):
        # Check if item pool is not empty and has required items
        pool = self.multiworld.itempool
        self.assertTrue(len(pool) > 0)

        bg_tracks = [item for item in pool if item.name == "Background Tracking"]
        self.assertEqual(len(bg_tracks), 1)


class TestTrekipelagoSnappingAndFallback(TrekipelagoTestBase):
    options = {
        # Highly incorrect options: interval larger than goal, uneven numbers, zero goal locations etc.
        "total_distance": 125,  # Will be snapped to 150
        "distance_interval": 333,  # Will be forcibly clamped down to rescue minimum required location limits
        "max_orbs": 0,  # Zero to force core generation onto distance only
        "goal": 0,
    }

    def test_safe_generation_fallback(self):
        # Fallback logic in _get_snapped_options() should handle this and rescue min 9 checks!
        world = self.multiworld.worlds[1]
        opts = world.get_snapped_options()

        self.assertTrue(opts["num_dist_locs"] >= 9)
        self.assertTrue(opts["total_dist"] % 50 == 0)
        self.assertTrue(opts["interval"] % 50 == 0)
        self.assertTrue(opts["interval"] <= opts["total_dist"])

        pool = self.multiworld.itempool
        self.assertTrue(len(pool) >= 9)
