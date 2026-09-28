from typing import TYPE_CHECKING

from BaseClasses import Entrance, Region

from .locations import (
    TrekipelagoLocation,
    distance_location_name,
    location_name_to_id,
    orb_location_name,
)

if TYPE_CHECKING:
    from . import TrekipelagoWorld


def create_regions(world: "TrekipelagoWorld") -> None:
    multiworld = world.multiworld
    player = world.player

    menu = Region("Menu", player, multiworld)
    world_region = Region("World", player, multiworld)

    layout_options = world.get_snapped_options()

    # Distance checks (the last one always equals the total distance)
    for distance_meters in layout_options["distances"]:
        location_name = distance_location_name(distance_meters)
        location = TrekipelagoLocation(
            player, location_name, location_name_to_id[location_name], world_region
        )
        world_region.locations.append(location)

    # Orb checks (ordinal names; thresholds go to the client via slot_data)
    for orb_index in range(1, layout_options["num_orb_locs"] + 1):
        location_name = orb_location_name(orb_index)
        location = TrekipelagoLocation(
            player, location_name, location_name_to_id[location_name], world_region
        )
        world_region.locations.append(location)

    menu_to_world = Entrance(player, "Start Trekking", menu)
    menu.exits.append(menu_to_world)
    menu_to_world.connect(world_region)

    multiworld.regions.append(menu)
    multiworld.regions.append(world_region)
