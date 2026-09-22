from typing import Dict

from BaseClasses import Location

from .options import MAX_DISTANCE_CONSTANT


class TrekipelagoLocation(Location):
    game = "Trekipelago"


TREKIPELAGO_LOCATION_BASE_ID = 890000000

# Distance locations pregenerated every 50 meters (lowest possible step configuration).
location_name_to_id: Dict[str, int] = {
    f"{dist}m": TREKIPELAGO_LOCATION_BASE_ID + dist
    for dist in range(50, MAX_DISTANCE_CONSTANT + 1, 50)
}

# Orb locations pregenerated starting from ID 890500001 to prevent distance overlaps.
location_name_to_id.update(
    {
        f"{orbs} Orbs": TREKIPELAGO_LOCATION_BASE_ID + 500000 + orbs
        for orbs in range(1, 10001)
    }
)
