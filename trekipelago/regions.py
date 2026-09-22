from BaseClasses import Entrance, Region

from .locations import TrekipelagoLocation, location_name_to_id


def create_regions(world):
    multiworld = world.multiworld
    player = world.player

    menu = Region("Menu", player, multiworld)
    world_region = Region("World", player, multiworld)

    opts = world.get_snapped_options()

    num_dist_locations = opts["num_dist_locs"]
    interval = opts["interval"]
    has_remainder = opts["has_remainder"]
    total_dist = opts["total_dist"]

    # Create locations for traveled distance (Distance checks)
    for i in range(1, num_dist_locations + 1):
        # If the interval does not divide the total distance evenly,
        # the last check matches the exact total distance to ensure completion.
        if i == num_dist_locations and has_remainder:
            dist = total_dist
        else:
            dist = i * interval

        loc_name = f"{dist}m"
        loc = TrekipelagoLocation(
            player, loc_name, location_name_to_id[loc_name], world_region
        )
        world_region.locations.append(loc)

    # Create locations for collected Orbs (Orb checks)
    max_orbs = opts["max_orbs"]
    orbs_per_reward = opts["orbs_per_reward"]
    num_orb_locations = opts["num_orb_locs"]

    if max_orbs > 0:
        for i in range(1, num_orb_locations + 1):
            orbs = i * orbs_per_reward
            loc_name = f"{orbs} Orbs"
            loc = TrekipelagoLocation(
                player, loc_name, location_name_to_id[loc_name], world_region
            )
            world_region.locations.append(loc)

    menu_to_world = Entrance(player, "Start Trekking", menu)
    menu.exits.append(menu_to_world)
    menu_to_world.connect(world_region)

    multiworld.regions.append(menu)
    multiworld.regions.append(world_region)
