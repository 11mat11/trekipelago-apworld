from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range

MAX_DISTANCE_KM = 500
# Normal distance checks use this grid to keep the datapackage small.
DISTANCE_STEP = 100
# A 1 km run needs a finer grid to provide at least 15 locations without orbs.
SHORT_DISTANCE_STEP = 50
SHORT_DISTANCE_MAX_M = 1000
# Hard cap on orb locations so the location table stays at 100 IDs regardless of YAML.
MAX_ORB_CHECKS = 100


class Goal(Choice):
    """The victory condition to complete the AP run."""

    display_name = "Goal"
    option_distance_only = 0
    option_distance_and_orbs = 1
    default = 0


class TotalDistance(Range):
    """The total distance you need to travel (in kilometers)."""

    display_name = "Total Distance (km)"
    range_start = 1
    range_end = MAX_DISTANCE_KM
    default = 5


class DistanceInterval(Range):
    """Distance interval per location check (in meters). Will snap to nearest 100!
    The final interval is shortened when needed to end exactly at the total distance.
    If fewer than 15 locations would be generated, the interval is reduced to 100 m,
    or 50 m for a 1 km run when necessary. The total distance is unchanged."""

    display_name = "Distance Interval (m)"
    range_start = DISTANCE_STEP
    range_end = 1000
    default = 500


class MaxOrbs(Range):
    """The maximum number of light orbs required if playing with Orb objectives."""

    display_name = "Max Orbs"
    range_start = 0
    range_end = 1000
    default = 50


class OrbsPerReward(Range):
    """Number of orbs collected to unlock a location check.
    At most 100 orb checks are generated; if max_orbs / orbs_per_reward would exceed
    that, this value is raised automatically.
    The final interval is shortened when needed to end exactly at max_orbs."""

    display_name = "Orbs per Reward"
    range_start = 1
    range_end = 100
    default = 5


class BuffRatio(Range):
    """Percentage of filler items that are buffs vs debuffs (traps). 0 to 100."""

    display_name = "Buff Ratio (%)"
    range_start = 0
    range_end = 100
    default = 70


@dataclass
class TrekipelagoOptions(PerGameCommonOptions):
    goal: Goal
    total_distance: TotalDistance
    distance_interval: DistanceInterval
    max_orbs: MaxOrbs
    orbs_per_reward: OrbsPerReward
    buff_ratio: BuffRatio
