from worlds.generic.Rules import add_item_rule, add_rule

from .locations import distance_location_name, orb_location_name


def _set_pacing_rules(multiworld, player, location_names):
    num_locations = len(location_names)
    def make_pacing_rule(bg: bool, pc: int, speed: int):
        return lambda state: (
            (not bg or state.has("Background Tracking", player))
            and (pc == 0 or state.has("Passive Collector", player, pc))
            and (speed == 0 or state.has("Progressive Speed", player, speed))
        )

    # Spread the 9 core progression items across each kind of check.
    # Slot k (1..9) becomes required from location index max(k+1, k*n//10 + 1).
    target_reqs = []
    for k in range(1, 10):
        loc_index = max(k + 1, (k * num_locations) // 10 + 1)
        target_reqs.append(loc_index)

    # Background Tracking is the first gate so screen-off tracking is
    # needed early. Sphere-zero placement is enforced separately by the world;
    # these access rules alone cannot guarantee it in a multiworld.
    req_bg_idx = target_reqs[0]
    req_speed_idx = [
        target_reqs[1],
        target_reqs[3],
        target_reqs[4],
        target_reqs[6],
        target_reqs[7],
    ]
    req_pc_idx = [target_reqs[2], target_reqs[5], target_reqs[8]]

    for i, location_name in enumerate(location_names, start=1):
        location = multiworld.get_location(location_name, player)

        req_bg = i >= req_bg_idx
        req_speed = sum(1 for idx in req_speed_idx if i >= idx)
        req_pc = sum(1 for idx in req_pc_idx if i >= idx)

        if req_bg or req_pc > 0 or req_speed > 0:
            add_rule(location, make_pacing_rule(req_bg, req_pc, req_speed))

        # Self-lock protection: if this location needs EVERY copy of an item that
        # exists in the pool, none of those copies may be placed here, otherwise the
        # location could never be reached to collect it.
        fully_required_items = []
        if req_bg:
            fully_required_items.append("Background Tracking")  # 1 in pool
        if req_pc == 3:
            fully_required_items.append("Passive Collector")  # 3 in pool
        if req_speed == 5:
            fully_required_items.append("Progressive Speed")  # 5 in pool

        if fully_required_items:
            # Only this player's copies matter; another Trekipelago player's items
            # with the same name are perfectly safe here.
            add_item_rule(
                location,
                lambda item, blocked=fully_required_items: (
                    item.player != player or item.name not in blocked
                ),
            )


def set_rules(world):
    multiworld = world.multiworld
    player = world.player
    opts = world.get_snapped_options()
    distances = opts["distances"]
    num_orb_locs = opts["num_orb_locs"]

    _set_pacing_rules(multiworld, player, [distance_location_name(d) for d in distances])
    _set_pacing_rules(multiworld, player, [orb_location_name(i) for i in range(1, num_orb_locs + 1)])

    # Victory Condition
    final_dist_loc = distance_location_name(distances[-1])

    if opts["goal"] == 0 or num_orb_locs == 0:  # Distance Only (or no orb checks)
        multiworld.completion_condition[player] = lambda state: state.can_reach(
            final_dist_loc, "Location", player
        )
    else:  # Distance and Orbs
        final_orb_loc = orb_location_name(num_orb_locs)
        multiworld.completion_condition[player] = lambda state: (
            state.can_reach(final_dist_loc, "Location", player)
            and state.can_reach(final_orb_loc, "Location", player)
        )
