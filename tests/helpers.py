from BaseClasses import MultiWorld
from Fill import balance_multiworld_progression, distribute_items_restrictive
from worlds.AutoWorld import call_all


def fill_multiworld(multiworld: MultiWorld) -> None:
    """Run fill, balancing, and final validation in the generator's order."""
    distribute_items_restrictive(multiworld)
    call_all(multiworld, "post_fill")
    if multiworld.players > 1:
        balance_multiworld_progression(multiworld)
    call_all(multiworld, "finalize_multiworld")
