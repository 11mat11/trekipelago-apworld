import math
from typing import Dict

from BaseClasses import Location

from .options import (
    DISTANCE_STEP,
    MAX_DISTANCE_KM,
    SHORT_DISTANCE_MAX_M,
    SHORT_DISTANCE_STEP,
    MaxOrbs,
    OrbsPerReward,
)


class TrekipelagoLocation(Location):
    game = "Trekipelago"


TREKIPELAGO_LOCATION_BASE_ID = 1111
MAX_DISTANCE_M = MAX_DISTANCE_KM * 1000

# Existing IDs contain regular distances, 100 orbs, then supplemental distances.
# Additional orb IDs must skip that supplemental distance block.
MAX_DISTANCE_CHECKS = MAX_DISTANCE_M // DISTANCE_STEP
ORB_LOCATION_ID_OFFSET = MAX_DISTANCE_CHECKS
LEGACY_ORB_LOCATION_COUNT = 100
SUPPLEMENTAL_DISTANCE_THRESHOLDS = range(
    SHORT_DISTANCE_STEP, SHORT_DISTANCE_MAX_M, DISTANCE_STEP
)
# Catalog capacity follows the option ranges; it does not adjust the chosen interval.
MAX_ORB_LOCATIONS = math.ceil(MaxOrbs.range_end / OrbsPerReward.range_start)


def distance_location_name(meters: int) -> str:
    return f"{meters}m"


def orb_location_name(index: int) -> str:
    return f"Orb Check {index}"


def _orb_location_id(index: int) -> int:
    location_id = TREKIPELAGO_LOCATION_BASE_ID + ORB_LOCATION_ID_OFFSET + index
    if index > LEGACY_ORB_LOCATION_COUNT:
        location_id += len(SUPPLEMENTAL_DISTANCE_THRESHOLDS)
    return location_id


# Distance locations pre-generated on a DISTANCE_STEP grid; ID = base + grid index.
location_name_to_id: Dict[str, int] = {
    distance_location_name(dist): TREKIPELAGO_LOCATION_BASE_ID + dist // DISTANCE_STEP
    for dist in range(DISTANCE_STEP, MAX_DISTANCE_M + 1, DISTANCE_STEP)
}

# Orb locations are ordinal ("Orb Check 1", "Orb Check 2", ...); the threshold for
# each check is sent to the client via slot_data.
location_name_to_id.update(
    {
        orb_location_name(index): _orb_location_id(index)
        for index in range(1, MAX_ORB_LOCATIONS + 1)
    }
)

# Only 1 km runs need the finer fallback grid. Keep its original ID block
# immediately after the first 100 orbs.
location_name_to_id.update(
    {
        distance_location_name(dist): (
            TREKIPELAGO_LOCATION_BASE_ID + ORB_LOCATION_ID_OFFSET + LEGACY_ORB_LOCATION_COUNT + i
        )
        for i, dist in enumerate(
            SUPPLEMENTAL_DISTANCE_THRESHOLDS, start=1
        )
    }
)
