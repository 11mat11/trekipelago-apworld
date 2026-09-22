from worlds.generic.Rules import add_rule


def set_rules(multiworld, player):
    world = multiworld.worlds[player]
    opts = world.get_snapped_options()

    total_dist = opts["total_dist"]
    interval = opts["interval"]
    num_dist_locs = opts["num_dist_locs"]
    has_remainder = opts["has_remainder"]

    def make_pacing_rule(bg: bool, pc: int, speed: int):
        return lambda state: (
            (not bg or state.has("Background Tracking", player))
            and (pc == 0 or state.has("Passive Collector", player, pc))
            and (speed == 0 or state.has("Progressive Speed", player, speed))
        )

    # Calculate safe bounding indexes for the 9 core progression items.
    # This completely prevents "FillError" logical deadlocks when there are very few locations.
    # k is the number of items required. loc_index guarantees we have at least k free locations prior.
    target_reqs = []
    for k in range(1, 10):
        # e.g., if we require 1 item (k=1), we can put the restriction on location 2 or later.
        loc_index = max(k + 1, (k * num_dist_locs) // 10 + 1)
        target_reqs.append(loc_index)

    req_bg_idx = target_reqs[0]
    req_speed_idx = [
        target_reqs[1],
        target_reqs[3],
        target_reqs[4],
        target_reqs[6],
        target_reqs[7],
    ]
    req_pc_idx = [target_reqs[2], target_reqs[5], target_reqs[8]]

    # 1. Distance Pacing Rules
    for i in range(1, num_dist_locs + 1):
        if i == num_dist_locs and has_remainder:
            dist = total_dist
        else:
            dist = i * interval

        loc_name = f"{dist}m"
        location = multiworld.get_location(loc_name, player)

        # Linear dependency: unlock distance step by step
        if i > 1:
            if i - 1 == num_dist_locs and has_remainder:
                prev_dist = (
                    total_dist  # Technically never happens, but added for clarity
                )
            else:
                prev_dist = (i - 1) * interval

            prev_loc_name = f"{prev_dist}m"
            add_rule(
                location,
                lambda state, prev=prev_loc_name: state.can_reach(
                    prev, "Location", player
                ),
            )

        # Pull dynamic requirements mapped to this specific iteration step securely
        req_bg = i >= req_bg_idx
        req_speed = sum(1 for idx in req_speed_idx if i >= idx)
        req_pc = sum(1 for idx in req_pc_idx if i >= idx)

        if req_bg or req_pc > 0 or req_speed > 0:
            add_rule(location, make_pacing_rule(req_bg, req_pc, req_speed))

    # 2. Linear Rules for Orbs (Collected sequentially)
    max_orbs = opts["max_orbs"]
    orbs_per_reward = opts["orbs_per_reward"]
    num_orb_locs = opts["num_orb_locs"]

    if max_orbs > 0:
        for i in range(1, num_orb_locs + 1):
            if i > 1:
                loc_name = f"{i * orbs_per_reward} Orbs"
                prev_loc_name = f"{(i - 1) * orbs_per_reward} Orbs"
                location = multiworld.get_location(loc_name, player)
                add_rule(
                    location,
                    lambda state, prev=prev_loc_name: state.can_reach(
                        prev, "Location", player
                    ),
                )

    # 3. Victory Condition
    final_dist_loc = (
        f"{total_dist}m" if has_remainder else f"{(num_dist_locs) * interval}m"
    )

    if opts["goal"] == 0:  # Distance Only
        multiworld.completion_condition[player] = lambda state: state.can_reach(
            final_dist_loc, "Location", player
        )
    else:  # Distance and Orbs
        final_orb_loc = (
            f"{(num_orb_locs) * orbs_per_reward} Orbs"
            if num_orb_locs > 0
            else final_dist_loc
        )

        multiworld.completion_condition[player] = lambda state: (
            state.can_reach(final_dist_loc, "Location", player)
            and (
                num_orb_locs == 0 or state.can_reach(final_orb_loc, "Location", player)
            )
        )
