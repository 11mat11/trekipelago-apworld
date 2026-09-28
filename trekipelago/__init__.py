import logging
import math
from typing import Any, Dict

from BaseClasses import CollectionState, Tutorial
from worlds.AutoWorld import WebWorld, World

from . import items, locations, regions, rules
from .items import TrekipelagoItem, get_filler_item_name, item_dictionary
from .locations import (
    TREKIPELAGO_LOCATION_BASE_ID,
    distance_location_name,
    orb_location_name,
)
from .options import DISTANCE_STEP, SHORT_DISTANCE_STEP, Goal, TrekipelagoOptions

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
    location_name_to_id = locations.location_name_to_id

    item_name_groups = {
        "Progression": set(items._PROGRESSION_ITEMS),
        "Buffs": {name for name, _ in items._buff_pool},
        "Traps": {name for name, _ in items._trap_pool},
    }
    location_name_groups = {
        "Distance": {
            name for name in locations.location_name_to_id.keys() if name.endswith("m")
        },
        "Orbs": {
            name
            for name in locations.location_name_to_id.keys()
            if name.startswith("Orb Check")
        },
    }

    _snapped_options: Dict[str, Any]

    def generate_early(self) -> None:
        self._snapped_options = self._snap_options()
        # Pacing rules alone do not constrain where another player's copy lands.
        # Request sphere-zero placement across the entire multiworld.
        starts_with_tracking = (
            self.options.start_inventory.value.get("Background Tracking", 0) > 0
            or getattr(self.options, "start_inventory_from_pool", {}).value.get(
                "Background Tracking", 0
            )
            > 0
        )
        if not starts_with_tracking:
            self.multiworld.early_items[self.player]["Background Tracking"] = 1

    def get_snapped_options(self) -> Dict[str, Any]:
        """Return the cached layout after rounding and applying generation limits."""
        if not hasattr(self, "_snapped_options"):
            self._snapped_options = self._snap_options()
        return self._snapped_options

    def _warn(self, message: str) -> None:
        logging.warning(
            f"Trekipelago ({self.multiworld.get_player_name(self.player)}): {message}"
        )

    def _snap_options(self) -> Dict[str, Any]:
        """
        Turn raw YAML options into a concrete, always-generatable layout:
        - total distance is given in km and converted to meters (always on the grid),
        - the interval is snapped to the DISTANCE_STEP grid and clamped to the total,
        - orb checks keep the requested orbs_per_reward, with a shorter final check if needed,
        - at least MIN_LOCATIONS locations are guaranteed for the core progression.
        Every adjustment is logged so the host can see what changed.
        """
        total_distance_meters = self.options.total_distance.value * 1000

        requested_interval_meters = self.options.distance_interval.value
        interval_meters = max(
            DISTANCE_STEP,
            int(requested_interval_meters / DISTANCE_STEP + 0.5) * DISTANCE_STEP,
        )
        interval_meters = min(interval_meters, total_distance_meters)
        if interval_meters != requested_interval_meters:
            self._warn(
                f"distance_interval {requested_interval_meters}m snapped to {interval_meters}m."
            )

        max_orbs = self.options.max_orbs.value
        orbs_per_reward = self.options.orbs_per_reward.value
        orb_location_count = math.ceil(max_orbs / orbs_per_reward)

        distance_location_count = math.ceil(total_distance_meters / interval_meters)

        # Keep the selected total distance and orb settings. A 1 km run with
        # fewer than 5 orb checks needs the supplemental 50 m distance grid.
        if distance_location_count + orb_location_count < MIN_LOCATIONS:
            interval_meters = DISTANCE_STEP
            distance_location_count = math.ceil(total_distance_meters / interval_meters)
            if distance_location_count + orb_location_count < MIN_LOCATIONS:
                interval_meters = SHORT_DISTANCE_STEP
                distance_location_count = math.ceil(
                    total_distance_meters / interval_meters
                )
            self._warn(
                f"fewer than {MIN_LOCATIONS} locations; distance_interval reduced to "
                f"{interval_meters}m ({distance_location_count} distance checks)."
            )

        # The last distance check always sits exactly on the total distance.
        distance_thresholds = [
            min(check_index * interval_meters, total_distance_meters)
            for check_index in range(1, distance_location_count + 1)
        ]
        # Like distance checks, the last orb check ends exactly at the configured maximum.
        orb_thresholds = [
            min(check_index * orbs_per_reward, max_orbs)
            for check_index in range(1, orb_location_count + 1)
        ]

        return {
            "total_dist": total_distance_meters,
            "interval": interval_meters,
            "max_orbs": max_orbs,
            "orbs_per_reward": orbs_per_reward,
            "goal": self.options.goal.value,
            "buff_ratio": self.options.buff_ratio.value,
            "num_dist_locs": distance_location_count,
            "num_orb_locs": orb_location_count,
            "distances": distance_thresholds,
            "orbs": orb_thresholds,
        }

    def create_regions(self) -> None:
        regions.create_regions(self)

    def create_items(self) -> None:
        layout_options = self.get_snapped_options()
        total_locations = (
            layout_options["num_dist_locs"] + layout_options["num_orb_locs"]
        )

        # Target progression items
        progression_pool = {
            "Background Tracking": 1,
            "Passive Collector": 3,
            "Progressive Speed": 5,
        }

        # Reduce pool for items given in start_inventory so they act as replacements rather than additions
        if hasattr(self.options, "start_inventory"):
            for item_name, amount in self.options.start_inventory.value.items():
                if item_name in progression_pool:
                    progression_pool[item_name] = max(
                        0, progression_pool[item_name] - amount
                    )

        item_names = []

        # 1. Guaranteed progression items
        for item_name, count in progression_pool.items():
            item_names.extend([item_name] * count)

        # 2. Filler items based on mobile app statistics
        buff_ratio = layout_options["buff_ratio"] / 100.0
        filler_item_count = total_locations - len(item_names)

        for _ in range(filler_item_count):
            item_names.append(get_filler_item_name(self.multiworld.random, buff_ratio))

        # 3. Add items to the world pool
        for item_name in item_names:
            self.multiworld.itempool.append(self.create_item(item_name))

    def create_item(self, name: str) -> TrekipelagoItem:
        """Create any catalog item for starting inventory, plando, or item links."""
        item_data = item_dictionary[name]
        return TrekipelagoItem(
            name, item_data["classification"], item_data["id"], self.player
        )

    def get_filler_item_name(self) -> str:
        """Replace removed pool items with repeatable buffs or traps, never progression."""
        return get_filler_item_name(self.random, self.options.buff_ratio.value / 100.0)

    def create_filler(self) -> TrekipelagoItem:
        return self.create_item(self.get_filler_item_name())

    def set_rules(self) -> None:
        rules.set_rules(self)

    def finalize_multiworld(self) -> None:
        # Early-item placement is best effort in core. Reject a late placement
        # (including plando) instead of silently shipping a seed without tracking.
        from Fill import FillError

        state = CollectionState(self.multiworld)
        if state.has("Background Tracking", self.player):
            return  # Already available in the player's starting inventory.
        tracking_locations = [
            location
            for location in self.multiworld.get_filled_locations()
            if location.item.player == self.player
            and location.item.name == "Background Tracking"
        ]
        if not tracking_locations or any(
            not location.can_reach(state) for location in tracking_locations
        ):
            placement = (
                ", ".join(str(location) for location in tracking_locations)
                or "not placed"
            )
            raise FillError(
                f"Trekipelago ({self.multiworld.get_player_name(self.player)}): "
                f"Background Tracking must be available in sphere 0; found at {placement}. "
                "Check plando, excluded locations, and local/non-local item settings."
            )

    def fill_slot_data(self) -> Dict[str, Any]:
        layout_options = self.get_snapped_options()
        return {
            "base_id": TREKIPELAGO_LOCATION_BASE_ID,
            "goal": (
                "distance_only"
                if layout_options["goal"] == Goal.option_distance_only
                else "distance_and_orbs"
            ),
            "distance_step": min(DISTANCE_STEP, layout_options["interval"]),
            "distance_interval": layout_options["interval"],
            "total_distance": layout_options["total_dist"],
            "max_orbs": layout_options["max_orbs"],
            "orbs_per_reward": layout_options["orbs_per_reward"],
            "buff_ratio": layout_options["buff_ratio"] / 100.0,
            # Explicit [location_id, threshold] pairs so the client never has to
            # re-derive the ID scheme.
            "distance_checks": [
                [
                    locations.location_name_to_id[
                        distance_location_name(distance_meters)
                    ],
                    distance_meters,
                ]
                for distance_meters in layout_options["distances"]
            ],
            "orb_checks": [
                [
                    locations.location_name_to_id[orb_location_name(check_index)],
                    orb_threshold,
                ]
                for check_index, orb_threshold in enumerate(
                    layout_options["orbs"], start=1
                )
            ],
        }
