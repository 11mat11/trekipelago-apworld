"""Preserve all seed ranges; merge only identical raw configurations."""
from dataclasses import dataclass
from functools import cached_property
import json

from worlds.trekipelago import TrekipelagoWorld


@dataclass
class GenerationCase:
    name: str
    options: dict
    players: int = 1
    seed: int = 0

    @cached_property
    def key(self):
        normalized = {
            name: option.from_any(self.options.get(name, option.default)).value
            for name, option in TrekipelagoWorld.options_dataclass.type_hints.items()
        }
        return self.players, self.seed, json.dumps(normalized, sort_keys=True, default=sorted)

    @property
    def id(self):
        return f"{self.name}-players={self.players}-seed={self.seed}"


# name, raw options, expected distance interval, distance thresholds, orb thresholds, orb interval
# The first seven entries replace the former WorldTestBase configurations.
LAYOUT_CASES = [
    ("standard", {"goal": 1}, 500, list(range(500, 5001, 500)), list(range(5, 51, 5)), 5),
    ("short-fallback", {"total_distance": 1, "distance_interval": 999, "max_orbs": 0},
     50, list(range(50, 1001, 50)), [], 5),
    ("distance-remainder", {"distance_interval": 900},
     900, [900, 1800, 2700, 3600, 4500, 5000], list(range(5, 51, 5)), 5),
    ("thousand-orbs", {"max_orbs": 1000, "orbs_per_reward": 1, "goal": 1},
     500, list(range(500, 5001, 500)), list(range(1, 1001)), 1),
    ("orb-remainder", {"max_orbs": 943, "orbs_per_reward": 100, "goal": 1},
     500, list(range(500, 5001, 500)), list(range(100, 901, 100)) + [943], 100),
    ("999-orbs", {"max_orbs": 999, "orbs_per_reward": 1, "goal": 1},
     500, list(range(500, 5001, 500)), list(range(1, 1000)), 1),
    ("single-orb", {"max_orbs": 43, "orbs_per_reward": 100, "goal": 1},
     100, list(range(100, 5001, 100)), [43], 100),
    ("short-zero", {"total_distance": 1, "distance_interval": 1000, "max_orbs": 0, "orbs_per_reward": 1},
     50, list(range(50, 1001, 50)), [], 1),
    ("short-four", {"total_distance": 1, "distance_interval": 1000, "max_orbs": 4, "orbs_per_reward": 1},
     50, list(range(50, 1001, 50)), [1, 2, 3, 4], 1),
    ("short-five", {"total_distance": 1, "distance_interval": 1000, "max_orbs": 5, "orbs_per_reward": 1},
     100, list(range(100, 1001, 100)), [1, 2, 3, 4, 5], 1),
    ("exactly-fifteen", {"max_orbs": 5, "orbs_per_reward": 1},
     500, list(range(500, 5001, 500)), [1, 2, 3, 4, 5], 1),
    ("fourteen-fallback", {"max_orbs": 4, "orbs_per_reward": 1},
     100, list(range(100, 5001, 100)), [1, 2, 3, 4], 1),
    ("hundred-orbs", {"max_orbs": 100, "orbs_per_reward": 1},
     500, list(range(500, 5001, 500)), list(range(1, 101)), 1),
    ("101-orbs", {"max_orbs": 101, "orbs_per_reward": 1},
     500, list(range(500, 5001, 500)), list(range(1, 102)), 1),
    ("large-exact-orb-interval", {"max_orbs": 999, "orbs_per_reward": 3},
     500, list(range(500, 5001, 500)), list(range(3, 1000, 3)), 3),
    ("large-shortened-orb-check", {"max_orbs": 1000, "orbs_per_reward": 3},
     500, list(range(500, 5001, 500)), list(range(3, 1000, 3)) + [1000], 3),
]

ORB_CONFIGS = [
    {"total_distance": 1, "distance_interval": 1000, "max_orbs": 14, "orbs_per_reward": 1},
    {"total_distance": 1, "distance_interval": 1000, "max_orbs": 5, "orbs_per_reward": 1},
    {"max_orbs": 43, "orbs_per_reward": 100},
    {"max_orbs": 50, "orbs_per_reward": 5},
    {"distance_interval": 900, "max_orbs": 943, "orbs_per_reward": 100},
    {"max_orbs": 999, "orbs_per_reward": 1},
]


def generation_cases():
    candidates = []
    for players in (1, 4):
        for km, interval in ((1, 1000), (2, 1000), (3, 200), (5, 500)):
            for seed in range(100):
                candidates.append(GenerationCase(
                    f"minimum-{km}km-{interval}m",
                    {"total_distance": km, "distance_interval": interval, "max_orbs": 0},
                    players, seed,
                ))
        for index, options in enumerate(ORB_CONFIGS):
            for seed in range(30):
                candidates.append(GenerationCase(f"orbs-{index}", {**options, "goal": 1}, players, seed))
        for max_orbs in (0, 50):
            for seed in range(10):
                candidates.append(GenerationCase(f"tracking-{max_orbs}", {"max_orbs": max_orbs}, players, seed))
        for seed in range(3):
            candidates.append(GenerationCase(
                "thousand-orbs", {"max_orbs": 1000, "orbs_per_reward": 1, "goal": 1},
                players, seed,
            ))
    for name, options, *_ in LAYOUT_CASES[:7]:
        candidates.append(GenerationCase(name, options))
    candidates.append(GenerationCase("non-local-tracking", {
        "max_orbs": 0, "non_local_items": {"Background Tracking"},
    }, 4))
    unique = {}
    for case in candidates:
        unique.setdefault(case.key, case)
    return list(unique.values())


GENERATION_CASES = generation_cases()
