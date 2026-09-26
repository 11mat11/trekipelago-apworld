from typing import Dict

from BaseClasses import Location

from .options import (
    DISTANCE_STEP, MAX_DISTANCE_KM, MAX_ORB_CHECKS,
    SHORT_DISTANCE_MAX_M, SHORT_DISTANCE_STEP,
)


class TrekipelagoLocation(Location):
    game = "Trekipelago"


TREKIPELAGO_LOCATION_BASE_ID = 890000000
MAX_DISTANCE_M = MAX_DISTANCE_KM * 1000

# Regular distance IDs occupy base+1 .. base+MAX_DISTANCE_CHECKS; orb IDs follow.
# Supplemental short-distance checks are appended after orbs to preserve both ranges.
MAX_DISTANCE_CHECKS = MAX_DISTANCE_M // DISTANCE_STEP
ORB_LOCATION_ID_OFFSET = MAX_DISTANCE_CHECKS


def distance_location_name(meters: int) -> str:
    return f"{meters}m"


def orb_location_name(index: int) -> str:
    return f"Orb Check {index}"


# Distance locations pre-generated on a DISTANCE_STEP grid; ID = base + grid index.
location_name_to_id: Dict[str, int] = {
    distance_location_name(dist): TREKIPELAGO_LOCATION_BASE_ID + dist // DISTANCE_STEP
    for dist in range(DISTANCE_STEP, MAX_DISTANCE_M + 1, DISTANCE_STEP)
}

# Orb locations are ordinal ("Orb Check 1".."Orb Check 100"); the orb threshold for
# each check is sent to the client via slot_data.
location_name_to_id.update(
    {
        orb_location_name(i): TREKIPELAGO_LOCATION_BASE_ID + ORB_LOCATION_ID_OFFSET + i
        for i in range(1, MAX_ORB_CHECKS + 1)
    }
)

# Only 1 km runs need the finer fallback grid. Append the ten missing thresholds
# without reassigning any existing distance or orb IDs.
location_name_to_id.update(
    {
        distance_location_name(dist): (
            TREKIPELAGO_LOCATION_BASE_ID + ORB_LOCATION_ID_OFFSET + MAX_ORB_CHECKS + i
        )
        for i, dist in enumerate(
            range(SHORT_DISTANCE_STEP, SHORT_DISTANCE_MAX_M, DISTANCE_STEP), start=1
        )
    }
)
