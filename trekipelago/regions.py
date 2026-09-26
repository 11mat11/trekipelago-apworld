from BaseClasses import Entrance, Region

from .locations import (
    TrekipelagoLocation,
    distance_location_name,
    location_name_to_id,
    orb_location_name,
)


def create_regions(world):
    multiworld = world.multiworld
    player = world.player

    menu = Region("Menu", player, multiworld)
    world_region = Region("World", player, multiworld)

    opts = world.get_snapped_options()

    # Distance checks (the last one always equals the total distance)
    for dist in opts["distances"]:
        loc_name = distance_location_name(dist)
        loc = TrekipelagoLocation(
            player, loc_name, location_name_to_id[loc_name], world_region
        )
        world_region.locations.append(loc)

    # Orb checks (ordinal names; thresholds go to the client via slot_data)
    for i in range(1, opts["num_orb_locs"] + 1):
        loc_name = orb_location_name(i)
        loc = TrekipelagoLocation(
            player, loc_name, location_name_to_id[loc_name], world_region
        )
        world_region.locations.append(loc)

    menu_to_world = Entrance(player, "Start Trekking", menu)
    menu.exits.append(menu_to_world)
    menu_to_world.connect(world_region)

    multiworld.regions.append(menu)
    multiworld.regions.append(world_region)
