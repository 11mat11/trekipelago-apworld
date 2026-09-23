from . import bases


class TestTrekipelagoStandard(bases.TrekipelagoTestBase):
    options = {
        "total_distance": 5,  # km
        "distance_interval": 500,  # m
        "max_orbs": 50,
        "orbs_per_reward": 5,
        "goal": 1,  # distance_and_orbs
    }

    def test_item_generation(self):
        pool = self.multiworld.itempool
        self.assertTrue(len(pool) > 0)

        bg_tracks = [item for item in pool if item.name == "Background Tracking"]
        self.assertEqual(len(bg_tracks), 1)

    def test_layout(self):
        opts = self.multiworld.worlds[1].get_snapped_options()
        self.assertEqual(opts["total_dist"], 5000)
        self.assertEqual(opts["interval"], 500)
        self.assertEqual(opts["distances"], list(range(500, 5001, 500)))
        self.assertEqual(opts["num_orb_locs"], 10)
        self.assertEqual(opts["orbs"], list(range(5, 51, 5)))
        self.assertEqual(len(self.multiworld.itempool), 20)

    def test_slot_data_maps_ids(self):
        world = self.multiworld.worlds[1]
        slot = world.fill_slot_data()
        self.assertEqual(len(slot["distance_checks"]), 10)
        self.assertEqual(len(slot["orb_checks"]), 10)
        self.assertEqual(slot["orb_checks"][0][1], 5)
        self.assertEqual(slot["orb_checks"][-1][1], 50)
        for loc_id, meters in slot["distance_checks"]:
            self.assertEqual(world.location_name_to_id[f"{meters}m"], loc_id)


class TestTrekipelagoSnappingAndFallback(bases.TrekipelagoTestBase):
    options = {
        "total_distance": 1,  # 1 km, lowest allowed
        "distance_interval": 999,  # off-grid, snaps to 1000 = whole distance -> 1 check
        "max_orbs": 0,  # force core progression onto distance checks only
        "goal": 0,
    }

    def test_safe_generation_fallback(self):
        world = self.multiworld.worlds[1]
        opts = world.get_snapped_options()

        # Total distance must never be altered by snapping (regression: it used to
        # drop below range_start).
        self.assertEqual(opts["total_dist"], 1000)
        self.assertGreaterEqual(opts["num_dist_locs"], 15)
        self.assertEqual(opts["interval"], 50)
        self.assertTrue(opts["interval"] <= opts["total_dist"])
        self.assertEqual(opts["distances"][-1], opts["total_dist"])

        pool = self.multiworld.itempool
        self.assertGreaterEqual(len(pool), 15)
        self.assertEqual(opts["distances"], list(range(50, 1001, 50)))
        self.assertEqual(world.fill_slot_data()["distance_step"], 50)
        self.assertEqual(
            [threshold for _, threshold in world.fill_slot_data()["distance_checks"]],
            opts["distances"],
        )

    def test_zero_orbs_disables_checks(self):
        world = self.multiworld.worlds[1]
        opts = world.get_snapped_options()
        self.assertEqual(opts["orbs"], [])
        self.assertEqual(opts["num_orb_locs"], 0)
        self.assertEqual(world.fill_slot_data()["orb_checks"], [])
        locations = self.multiworld.get_locations(1)
        self.assertFalse(any(loc.name.startswith("Orb Check ") for loc in locations))
        self.assertEqual(len(locations), opts["num_dist_locs"])
        self.assertEqual(len(self.multiworld.itempool), len(locations))


class TestTrekipelagoRemainder(bases.TrekipelagoTestBase):
    options = {
        "total_distance": 5,
        "distance_interval": 900,  # 5000 % 900 != 0 -> last check lands on 5000m
        "max_orbs": 50,  # orb checks keep the total >= 15 so no fallback kicks in
        "orbs_per_reward": 5,
    }

    def test_last_check_is_total_distance(self):
        opts = self.multiworld.worlds[1].get_snapped_options()
        self.assertEqual(opts["distances"], [900, 1800, 2700, 3600, 4500, 5000])
        self.assertIsNotNone(self.multiworld.get_location("5000m", 1))
        slot = self.multiworld.worlds[1].fill_slot_data()
        self.assertEqual([threshold for _, threshold in slot["distance_checks"]], opts["distances"])
        self.assertEqual(opts["distances"][-1] - opts["distances"][-2], 500)


class TestTrekipelagoOrbCap(bases.TrekipelagoTestBase):
    options = {
        "total_distance": 5,
        "distance_interval": 500,
        "max_orbs": 1000,
        "orbs_per_reward": 1,  # would be 1000 checks -> capped to 100
        "goal": 1,
    }

    def test_orb_checks_capped(self):
        opts = self.multiworld.worlds[1].get_snapped_options()
        self.assertEqual(opts["num_orb_locs"], 100)
        self.assertEqual(opts["orbs_per_reward"], 10)
        self.assertEqual(opts["orbs"][-1], 1000)
        self.assertIsNotNone(self.multiworld.get_location("Orb Check 100", 1))


class TestTrekipelagoOrbRemainder(bases.TrekipelagoTestBase):
    options = {"max_orbs": 943, "orbs_per_reward": 100, "goal": 1}

    def test_last_orb_interval_is_remainder(self):
        world = self.multiworld.worlds[1]
        opts = world.get_snapped_options()
        expected = list(range(100, 901, 100)) + [943]
        self.assertEqual(opts["orbs"], expected)
        self.assertEqual(opts["num_orb_locs"], 10)
        self.assertEqual(opts["orbs"][-1] - opts["orbs"][-2], 43)
        self.assertEqual(
            world.fill_slot_data()["orb_checks"],
            [[world.location_name_to_id[f"Orb Check {i}"], threshold]
             for i, threshold in enumerate(expected, start=1)],
        )
        self.assertIsNotNone(self.multiworld.get_location("Orb Check 10", 1))
        self.assertEqual(len(self.multiworld.get_locations(1)), opts["num_dist_locs"] + 10)
        self.assertEqual(len(self.multiworld.itempool), opts["num_dist_locs"] + 10)


class TestTrekipelagoOrbCapRemainder(bases.TrekipelagoTestBase):
    options = {"max_orbs": 999, "orbs_per_reward": 1, "goal": 1}

    def test_capped_checks_include_maximum(self):
        opts = self.multiworld.worlds[1].get_snapped_options()
        self.assertEqual(opts["orbs_per_reward"], 10)
        self.assertEqual(opts["num_orb_locs"], 100)
        self.assertEqual(opts["orbs"], list(range(10, 991, 10)) + [999])
        self.assertIsNotNone(self.multiworld.get_location("Orb Check 100", 1))


class TestTrekipelagoOrbBelowInterval(bases.TrekipelagoTestBase):
    options = {"max_orbs": 43, "orbs_per_reward": 100, "goal": 1}

    def test_single_partial_check(self):
        world = self.multiworld.worlds[1]
        opts = world.get_snapped_options()
        self.assertEqual(opts["orbs"], [43])
        self.assertEqual(opts["num_orb_locs"], 1)
        self.assertEqual(world.fill_slot_data()["orb_checks"],
                         [[world.location_name_to_id["Orb Check 1"], 43]])
        self.assertIsNotNone(self.multiworld.get_location("Orb Check 1", 1))
