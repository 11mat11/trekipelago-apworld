import math
from typing import Any, Dict

from BaseClasses import Item, MultiWorld, Tutorial
from worlds.AutoWorld import WebWorld, World

from .items import (
    TREKIPELAGO_ITEM_BASE_ID,
    TrekipelagoItem,
    get_filler_item_name,
    item_dictionary,
)
from .locations import (
    TREKIPELAGO_LOCATION_BASE_ID,
    TrekipelagoLocation,
    location_name_to_id,
)
from .options import TrekipelagoOptions
from .regions import create_regions
from .rules import set_rules


class TrekipelagoWeb(WebWorld):
    theme = "ocean"
    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the Trekipelago mobile app for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Mateusz"],
    )
    tutorials = [setup_en]


class TrekipelagoWorld(World):
    """
    Trekipelago is a GPS-based mobile game. Walk, run, or cycle in the real world
    to earn items in Archipelago!
    """

    game = "Trekipelago"
    options_dataclass = TrekipelagoOptions
    options_dict = TrekipelagoOptions

    topology_present = False
    data_version = 1
    web = TrekipelagoWeb()

    item_name_to_id = {name: data["id"] for name, data in item_dictionary.items()}
    location_name_to_id = location_name_to_id

    def _get_option_value(self, option_name: str) -> Any:
        if hasattr(self, "options") and hasattr(self.options, option_name):
            return getattr(self.options, option_name).value
        return getattr(self.multiworld, option_name)[self.player].value

    def get_snapped_options(self) -> Dict[str, Any]:
        """
        Intelligently snaps user YAML options to guarantee logic completion
        without throwing setup errors. Also validates there are at least 9
        core progression locations.
        """
        total_dist = self._get_option_value("total_distance")
        interval = self._get_option_value("distance_interval")
        max_orbs = self._get_option_value("max_orbs")
        orbs_per_reward = self._get_option_value("orbs_per_reward")
        goal = self._get_option_value("goal")
        buff_ratio = self._get_option_value("buff_ratio")

        # Snap interval and distance to a multiple of 50 (required for pre-generated dictionary)
        interval = max(50, round(interval / 50) * 50)
        total_dist = max(50, round(total_dist / 50) * 50)

        # Fallback if interval is larger than goal
        if interval > total_dist:
            interval = total_dist

        num_dist_locations = total_dist // interval
        has_remainder = total_dist % interval != 0
        if has_remainder:
            num_dist_locations += 1

        num_orb_locations = (max_orbs // orbs_per_reward) if max_orbs > 0 else 0
        total_locations = num_dist_locations + num_orb_locations

        # Auto-adjust: guarantee minimum 9 locations for core progression items!
        if total_locations < 9:
            required_dist_locs = 9 - num_orb_locations
            if required_dist_locs > 0:
                new_interval = total_dist // required_dist_locs
                new_interval = max(50, round(new_interval / 50) * 50)

                # If we rounded down and still lack locations (e.g., from 100) or it's < 50
                if (
                    total_dist // max(50, new_interval)
                    + (1 if total_dist % max(50, new_interval) != 0 else 0)
                    < required_dist_locs
                ):
                    new_interval = 50
                    # Force total_dist up to fit 9 checks at 50 units each
                    total_dist = required_dist_locs * new_interval

                interval = new_interval
                num_dist_locations = total_dist // interval
                has_remainder = total_dist % interval != 0
                if has_remainder:
                    num_dist_locations += 1

        return {
            "total_dist": total_dist,
            "interval": interval,
            "max_orbs": max_orbs,
            "orbs_per_reward": orbs_per_reward,
            "goal": goal,
            "buff_ratio": buff_ratio,
            "num_dist_locs": num_dist_locations,
            "num_orb_locs": num_orb_locations,
            "has_remainder": has_remainder,
        }

    def create_regions(self):
        create_regions(self)

    def create_items(self):
        opts = self.get_snapped_options()
        total_locations = opts["num_dist_locs"] + opts["num_orb_locs"]

        items_to_add = []

        # 1. Guaranteed progression items (9 items)
        items_to_add.append("Background Tracking")
        items_to_add.extend(["Passive Collector"] * 3)
        items_to_add.extend(["Progressive Speed"] * 5)

        # 2. Filler items based on mobile app statistics
        buff_ratio = opts["buff_ratio"] / 100.0
        remaining = total_locations - len(items_to_add)

        for _ in range(remaining):
            items_to_add.append(
                get_filler_item_name(self.multiworld.random, buff_ratio)
            )

        # 3. Add items to the world pool
        for item_name in items_to_add:
            item_data = item_dictionary[item_name]
            item = TrekipelagoItem(
                item_name, item_data["classification"], item_data["id"], self.player
            )
            self.multiworld.itempool.append(item)

    def set_rules(self):
        set_rules(self.multiworld, self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        opts = self.get_snapped_options()
        return {
            "base_id": TREKIPELAGO_LOCATION_BASE_ID,
            "goal": "distance_only" if opts["goal"] == 0 else "distance_and_orbs",
            "distance_interval": opts["interval"],
            "total_distance": opts["total_dist"],
            "max_orbs": opts["max_orbs"],
            "orbs_per_reward": opts["orbs_per_reward"],
            "buff_ratio": opts["buff_ratio"] / 100.0,
        }
