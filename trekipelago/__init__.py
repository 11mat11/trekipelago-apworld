import logging
import math
from typing import Any, Dict

from BaseClasses import CollectionState, Tutorial
from worlds.AutoWorld import WebWorld, World

from .items import TrekipelagoItem, get_filler_item_name, item_dictionary
from .locations import (
    TREKIPELAGO_LOCATION_BASE_ID,
    TrekipelagoLocation,
    distance_location_name,
    location_name_to_id,
    orb_location_name,
)
from .options import DISTANCE_STEP, MAX_ORB_CHECKS, SHORT_DISTANCE_STEP, TrekipelagoOptions
from .regions import create_regions
from .rules import set_rules

# Room for the 9 core progression items plus at least 6 filler items.
MIN_LOCATIONS = 15


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
    options: TrekipelagoOptions

    topology_present = False
    web = TrekipelagoWeb()

    item_name_to_id = {name: data["id"] for name, data in item_dictionary.items()}
    location_name_to_id = location_name_to_id

    _snapped: Dict[str, Any]

    def generate_early(self) -> None:
        self._snapped = self._snap_options()
        # Pacing rules alone do not constrain where another player's copy lands.
        # Request sphere-zero placement across the entire multiworld.
        self.multiworld.early_items[self.player]["Background Tracking"] = 1

    def get_snapped_options(self) -> Dict[str, Any]:
        if not hasattr(self, "_snapped"):
            self._snapped = self._snap_options()
        return self._snapped

    def _warn(self, message: str) -> None:
        logging.warning(
            f"Trekipelago ({self.multiworld.get_player_name(self.player)}): {message}"
        )

    def _snap_options(self) -> Dict[str, Any]:
        """
        Turn raw YAML options into a concrete, always-generatable layout:
        - total distance is given in km and converted to meters (always on the grid),
        - the interval is snapped to the DISTANCE_STEP grid and clamped to the total,
        - orb checks are capped at MAX_ORB_CHECKS by raising orbs_per_reward,
        - at least MIN_LOCATIONS locations are guaranteed for the core progression.
        Every adjustment is logged so the host can see what changed.
        """
        total_dist = self.options.total_distance.value * 1000

        requested_interval = self.options.distance_interval.value
        interval = max(
            DISTANCE_STEP, int(requested_interval / DISTANCE_STEP + 0.5) * DISTANCE_STEP
        )
        interval = min(interval, total_dist)
        if interval != requested_interval:
            self._warn(f"distance_interval {requested_interval}m snapped to {interval}m.")

        max_orbs = self.options.max_orbs.value
        orbs_per_reward = self.options.orbs_per_reward.value
        num_orb_locations = 0
        if max_orbs > 0:
            min_per_reward = math.ceil(max_orbs / MAX_ORB_CHECKS)
            if orbs_per_reward < min_per_reward:
                self._warn(
                    f"orbs_per_reward raised from {orbs_per_reward} to {min_per_reward} "
                    f"to stay within {MAX_ORB_CHECKS} orb checks."
                )
                orbs_per_reward = min_per_reward
            num_orb_locations = math.ceil(max_orbs / orbs_per_reward)

        num_dist_locations = math.ceil(total_dist / interval)

        # Keep the selected total distance and orb settings. A 1 km run with
        # fewer than 5 orb checks needs the supplemental 50 m distance grid.
        if num_dist_locations + num_orb_locations < MIN_LOCATIONS:
            interval = DISTANCE_STEP
            num_dist_locations = math.ceil(total_dist / interval)
            if num_dist_locations + num_orb_locations < MIN_LOCATIONS:
                interval = SHORT_DISTANCE_STEP
                num_dist_locations = math.ceil(total_dist / interval)
            self._warn(
                f"fewer than {MIN_LOCATIONS} locations; distance_interval reduced to "
                f"{interval}m ({num_dist_locations} distance checks)."
            )

        # The last distance check always sits exactly on the total distance.
        distances = [min(i * interval, total_dist) for i in range(1, num_dist_locations + 1)]
        # Like distance checks, the last orb check ends exactly at the configured maximum.
        orbs = [min(i * orbs_per_reward, max_orbs) for i in range(1, num_orb_locations + 1)]

        return {
            "total_dist": total_dist,
            "interval": interval,
            "max_orbs": max_orbs,
            "orbs_per_reward": orbs_per_reward,
            "goal": self.options.goal.value,
            "buff_ratio": self.options.buff_ratio.value,
            "num_dist_locs": num_dist_locations,
            "num_orb_locs": num_orb_locations,
            "distances": distances,
            "orbs": orbs,
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
        set_rules(self)

    def finalize_multiworld(self) -> None:
        # Early-item placement is best effort in core. Reject a late placement
        # (including plando) instead of silently shipping a seed without tracking.
        from Fill import FillError

        state = CollectionState(self.multiworld)
        if state.has("Background Tracking", self.player):
            return  # Already available in the player's starting inventory.
        locations = [
            location for location in self.multiworld.get_filled_locations()
            if location.item.player == self.player
            and location.item.name == "Background Tracking"
        ]
        if not locations or any(not location.can_reach(state) for location in locations):
            placement = ", ".join(str(location) for location in locations) or "not placed"
            raise FillError(
                f"Trekipelago ({self.multiworld.get_player_name(self.player)}): "
                f"Background Tracking must be available in sphere 0; found at {placement}. "
                "Check plando, excluded locations, and local/non-local item settings."
            )

    def fill_slot_data(self) -> Dict[str, Any]:
        opts = self.get_snapped_options()
        return {
            "base_id": TREKIPELAGO_LOCATION_BASE_ID,
            "goal": "distance_only" if opts["goal"] == 0 else "distance_and_orbs",
            "distance_step": min(DISTANCE_STEP, opts["interval"]),
            "distance_interval": opts["interval"],
            "total_distance": opts["total_dist"],
            "max_orbs": opts["max_orbs"],
            "orbs_per_reward": opts["orbs_per_reward"],
            "buff_ratio": opts["buff_ratio"] / 100.0,
            # Explicit [location_id, threshold] pairs so the client never has to
            # re-derive the ID scheme.
            "distance_checks": [
                [location_name_to_id[distance_location_name(d)], d]
                for d in opts["distances"]
            ],
            "orb_checks": [
                [location_name_to_id[orb_location_name(i)], orbs]
                for i, orbs in enumerate(opts["orbs"], start=1)
            ],
        }
