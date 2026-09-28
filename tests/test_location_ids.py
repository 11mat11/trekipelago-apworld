import unittest

from worlds.trekipelago.locations import location_name_to_id, TREKIPELAGO_LOCATION_BASE_ID


class TestLocationIds(unittest.TestCase):
    def test_supplemental_ids_preserve_existing_mappings(self):
        for distance in range(100, 500001, 100):
            self.assertEqual(location_name_to_id[f"{distance}m"],
                             TREKIPELAGO_LOCATION_BASE_ID + distance // 100)
        for index in range(1, 101):
            self.assertEqual(location_name_to_id[f"Orb Check {index}"],
                             TREKIPELAGO_LOCATION_BASE_ID + 5000 + index)
        self.assertEqual(len(location_name_to_id), len(set(location_name_to_id.values())))
        for index, distance in enumerate(range(50, 1000, 100), start=1):
            self.assertEqual(location_name_to_id[f"{distance}m"],
                             TREKIPELAGO_LOCATION_BASE_ID + 5100 + index)

    def test_new_orb_ids_skip_the_existing_short_distance_block(self):
        for index in range(101, 1001):
            self.assertEqual(location_name_to_id[f"Orb Check {index}"],
                             TREKIPELAGO_LOCATION_BASE_ID + 5000 + index + 10)
        self.assertEqual(location_name_to_id["Orb Check 100"] + 11,
                         location_name_to_id["Orb Check 101"])
        self.assertEqual(len(location_name_to_id), 5000 + 1000 + 10)
        self.assertEqual(len(location_name_to_id), len(set(location_name_to_id.values())))
