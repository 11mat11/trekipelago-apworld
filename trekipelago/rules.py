from typing import TYPE_CHECKING, Callable, Sequence

from BaseClasses import CollectionState, Item, MultiWorld
from worlds.generic.Rules import add_item_rule, add_rule

from .locations import distance_location_name, orb_location_name
from .options import Goal

if TYPE_CHECKING:
    from . import TrekipelagoWorld

# Percentages apply separately to actual distance and orb thresholds.
EARLY_GAME_END_PERCENT = 20
LATE_GAME_START_PERCENT = 80


def _set_foreign_item_rules(
    world: "TrekipelagoWorld",
    location_names: Sequence[str],
    thresholds: Sequence[int],
    final_threshold: int,
) -> None:
    """Keep requested early items near the start and foreign progression out of the end."""
    multiworld = world.multiworld
    player = world.player

    def make_item_rule(early_game: bool, late_game: bool) -> Callable[[Item], bool]:
        def can_place_item(item: Item) -> bool:
            if item.player == player:
                return True
            if late_game and item.advancement:
                return False

            # Read requests when placing the item, after every world has set its rules.
            requested_early = (
                multiworld.early_items[item.player].get(item.name, 0) > 0
                or multiworld.local_early_items[item.player].get(item.name, 0) > 0
            )
            return early_game or not requested_early

        return can_place_item

    for location_name, threshold in zip(location_names, thresholds):
        early_game = threshold * 100 <= final_threshold * EARLY_GAME_END_PERCENT
        late_game = threshold * 100 > final_threshold * LATE_GAME_START_PERCENT
        location = multiworld.get_location(location_name, player)
        add_item_rule(location, make_item_rule(early_game, late_game))


def _set_pacing_rules(
    multiworld: MultiWorld, player: int, location_names: Sequence[str]
) -> None:
    location_count = len(location_names)

    def make_pacing_rule(
        requires_background_tracking: bool,
        required_passive_collectors: int,
        required_speed_upgrades: int,
    ) -> Callable[[CollectionState], bool]:
        return lambda state: (
            (not requires_background_tracking or state.has("Background Tracking", player))
            and (
                required_passive_collectors == 0
                or state.has("Passive Collector", player, required_passive_collectors)
            )
            and (
                required_speed_upgrades == 0
                or state.has("Progressive Speed", player, required_speed_upgrades)
            )
        )

    # Spread the 9 core progression items across each kind of check.
    # Each progression slot gates roughly the next tenth of the checks, but
    # leaves at least one earlier location for each item needed to reach it.
    progression_thresholds = []
    for progression_slot in range(1, 10):
        location_index = max(
            progression_slot + 1, (progression_slot * location_count) // 10 + 1
        )
        progression_thresholds.append(location_index)

    # Background Tracking is the first gate so screen-off tracking is
    # needed early. Sphere-zero placement is enforced separately by the world;
    # these access rules alone cannot guarantee it in a multiworld.
    background_tracking_threshold = progression_thresholds[0]
    speed_upgrade_thresholds = [
        progression_thresholds[1],
        progression_thresholds[3],
        progression_thresholds[4],
        progression_thresholds[6],
        progression_thresholds[7],
    ]
    passive_collector_thresholds = [
        progression_thresholds[2],
        progression_thresholds[5],
        progression_thresholds[8],
    ]

    for location_index, location_name in enumerate(location_names, start=1):
        location = multiworld.get_location(location_name, player)

        requires_background_tracking = location_index >= background_tracking_threshold
        required_speed_upgrades = sum(
            1 for threshold in speed_upgrade_thresholds if location_index >= threshold
        )
        required_passive_collectors = sum(
            1 for threshold in passive_collector_thresholds if location_index >= threshold
        )

        if (
            requires_background_tracking
            or required_passive_collectors > 0
            or required_speed_upgrades > 0
        ):
            add_rule(
                location,
                make_pacing_rule(
                    requires_background_tracking,
                    required_passive_collectors,
                    required_speed_upgrades,
                ),
            )

        # Self-lock protection: if this location needs EVERY copy of an item that
        # exists in the pool, none of those copies may be placed here, otherwise the
        # location could never be reached to collect it.
        fully_required_items = []
        if requires_background_tracking:
            fully_required_items.append("Background Tracking")  # 1 in pool
        if required_passive_collectors == 3:
            fully_required_items.append("Passive Collector")  # 3 in pool
        if required_speed_upgrades == 5:
            fully_required_items.append("Progressive Speed")  # 5 in pool

        if fully_required_items:
            # Only this player's copies can cause this self-lock. Foreign items
            # have separate placement limits based on distance and orb progress.
            add_item_rule(
                location,
                lambda item, blocked=fully_required_items: (
                    item.player != player or item.name not in blocked
                ),
            )


def set_rules(world: "TrekipelagoWorld") -> None:
    multiworld = world.multiworld
    player = world.player
    layout_options = world.get_snapped_options()
    distance_thresholds = layout_options["distances"]
    orb_location_count = layout_options["num_orb_locs"]

    distance_location_names = [
        distance_location_name(distance_meters) for distance_meters in distance_thresholds
    ]
    orb_location_names = [
        orb_location_name(orb_index) for orb_index in range(1, orb_location_count + 1)
    ]
    _set_pacing_rules(multiworld, player, distance_location_names)
    _set_pacing_rules(multiworld, player, orb_location_names)
    _set_foreign_item_rules(
        world, distance_location_names, distance_thresholds, layout_options["total_dist"]
    )
    _set_foreign_item_rules(
        world, orb_location_names, layout_options["orbs"], layout_options["max_orbs"]
    )

    # Without orb checks, reaching the final distance is enough for either goal.
    final_distance_location_name = distance_location_name(distance_thresholds[-1])

    if layout_options["goal"] == Goal.option_distance_only or orb_location_count == 0:
        multiworld.completion_condition[player] = lambda state: state.can_reach(
            final_distance_location_name, "Location", player
        )
    else:  # Distance and Orbs
        final_orb_location_name = orb_location_name(orb_location_count)
        multiworld.completion_condition[player] = lambda state: (
            state.can_reach(final_distance_location_name, "Location", player)
            and state.can_reach(final_orb_location_name, "Location", player)
        )
