from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range

MAX_DISTANCE_CONSTANT = 500000  # 500 km


class Goal(Choice):
    """The victory condition to complete the AP run."""

    display_name = "Goal"
    option_distance_only = 0
    option_distance_and_orbs = 1
    default = 0


class TotalDistance(Range):
    """The total distance you need to travel (in meters)."""

    display_name = "Total Distance"
    range_start = 500
    range_end = MAX_DISTANCE_CONSTANT
    default = 5000


class DistanceInterval(Range):
    """Distance interval per location check (in meters). Will snap to nearest 50!"""

    display_name = "Distance Interval"
    range_start = 50
    range_end = 10000
    default = 500


class MaxOrbs(Range):
    """The maximum number of light orbs required if playing with Orb objectives."""

    display_name = "Max Orbs"
    range_start = 0
    range_end = 10000
    default = 50


class OrbsPerReward(Range):
    """Number of orbs collected to unlock a location check."""

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
