import unittest

import pytest

from BaseClasses import Item, ItemClassification
from test.general import setup_multiworld
from worlds.apquest import APQuestWorld
from worlds.generic.Rules import locality_rules
from worlds.trekipelago import TrekipelagoWorld

from .helpers import collect_spheres, fill_multiworld


@pytest.mark.parametrize("location_name,allows_early,allows_progression", [
    ("1000m", True, True),
    ("1500m", False, True),
    ("4000m", False, True),
    ("4500m", False, False),
    ("5000m", False, False),
    ("Orb Check 2", True, True),
    ("Orb Check 3", False, True),
    ("Orb Check 8", False, True),
    ("Orb Check 9", False, False),
    ("Orb Check 10", False, False),
])
def test_foreign_item_placement_boundaries(location_name, allows_early, allows_progression):
    multiworld = setup_multiworld([TrekipelagoWorld] * 2, seed=0)
    location = multiworld.get_location(location_name, 1)
    foreign_item = Item("Test Item", ItemClassification.progression, 1, 2)
    assert location.item_rule(foreign_item) == allows_progression

    for classification in (ItemClassification.useful, ItemClassification.filler, ItemClassification.trap):
        foreign_item.classification = classification
        assert location.item_rule(foreign_item)

    # Requests added after set_rules must be honored, including non-progression items.
    for requests in (multiworld.early_items, multiworld.local_early_items):
        requests[2][foreign_item.name] = 1
        for classification in (ItemClassification.progression, ItemClassification.useful):
            foreign_item.classification = classification
            assert location.item_rule(foreign_item) == allows_early
        requests[2].clear()

    local_item = Item("Local Test Item", ItemClassification.progression, 2, 1)
    assert location.item_rule(local_item)


@pytest.mark.parametrize("options,location_name,allows_progression", [
    ({"max_orbs": 43, "orbs_per_reward": 100}, "Orb Check 1", False),
    ({"total_distance": 1, "distance_interval": 1000, "max_orbs": 14,
      "orbs_per_reward": 1}, "1000m", False),
    ({"distance_interval": 900}, "3600m", True),
    ({"distance_interval": 900}, "4500m", False),
    ({"max_orbs": 43, "orbs_per_reward": 5}, "Orb Check 7", False),
    ({"max_orbs": 43, "orbs_per_reward": 5}, "Orb Check 9", False),
    ({"max_orbs": 1000, "orbs_per_reward": 1}, "Orb Check 800", True),
    ({"max_orbs": 1000, "orbs_per_reward": 1}, "Orb Check 801", False),
    ({"max_orbs": 1000, "orbs_per_reward": 1}, "Orb Check 1000", False),
])
def test_placement_uses_actual_thresholds(options, location_name, allows_progression):
    multiworld = setup_multiworld([TrekipelagoWorld] * 2, seed=0, options=options)
    foreign_item = Item("Test Item", ItemClassification.progression, 1, 2)
    assert multiworld.get_location(location_name, 1).item_rule(foreign_item) == allows_progression


class TestMixedGamePlacement(unittest.TestCase):
    def test_foreign_progression_stays_out_of_late_checks_after_balancing(self):
        configurations = [
            {},
            {"max_orbs": 0},
            {"max_orbs": 1000, "orbs_per_reward": 1, "goal": 1},
            {"max_orbs": 43, "orbs_per_reward": 100},
            {"distance_interval": 900, "max_orbs": 43, "orbs_per_reward": 5},
            {"total_distance": 1, "distance_interval": 1000, "max_orbs": 14,
             "orbs_per_reward": 1},
        ]
        for options in configurations:
            for request_early_key in (False, True):
                for seed in range(30):
                    with self.subTest(options=options, early_key=request_early_key, seed=seed):
                        multiworld = setup_multiworld(
                            [TrekipelagoWorld, APQuestWorld], seed=seed,
                            options=[options.copy(), {"non_local_items": {"Key"}}],
                        )
                        if request_early_key:
                            multiworld.early_items[2]["Key"] = 1
                        locality_rules(multiworld)
                        fill_multiworld(multiworld)
                        spheres, final_state = collect_spheres(multiworld)
                        self.assertTrue(multiworld.has_beaten_game(final_state))
                        layout = multiworld.worlds[1].get_snapped_options()
                        groups = [
                            ([(f"{distance}m", distance) for distance in layout["distances"]],
                             layout["total_dist"]),
                            ([(f"Orb Check {index}", count)
                              for index, count in enumerate(layout["orbs"], start=1)],
                             layout["max_orbs"]),
                        ]
                        key_found = False
                        for checks, total in groups:
                            for name, threshold in checks:
                                location = multiworld.get_location(name, 1)
                                item = location.item
                                if item.player == 2 and item.advancement:
                                    self.assertLessEqual(threshold * 100, total * 80)
                                if item.player == 2 and item.name == "Key":
                                    key_found = True
                                    if request_early_key:
                                        self.assertLessEqual(threshold * 100, total * 20)
                                        self.assertEqual(spheres[location], 0)
                        self.assertTrue(key_found)
