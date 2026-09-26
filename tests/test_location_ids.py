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
        for distance in range(50, 1000, 100):
            self.assertIn(f"{distance}m", location_name_to_id)
