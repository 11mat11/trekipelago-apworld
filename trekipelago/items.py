import random
from typing import Dict, List, Tuple, TypedDict

from BaseClasses import Item, ItemClassification


class TrekipelagoItem(Item):
    game = "Trekipelago"


class ItemData(TypedDict, total=False):
    id: int
    classification: ItemClassification
    weight_buff: float
    weight_trap: float


TREKIPELAGO_ITEM_BASE_ID = 890000000

# Duration variants share the base weight of their effect; the split mirrors the
# drop statistics of the mobile app.
_DURATION_SPLIT: List[Tuple[str, float]] = [("5m", 0.65), ("15m", 0.25), ("30m", 0.10)]

_progression = ["Background Tracking", "Passive Collector", "Progressive Speed"]

# (effect name, base weight)
_timed_buffs = [
    ("Speed Boost", 30.0),
    ("Double Distance", 25.0),
    ("Double Orb Spawns", 25.0),
    ("Double Collected Orbs", 20.0),
]
_timed_traps = [
    ("Trap: Slow Movement", 25.0),
    ("Trap: Half Distance", 25.0),
    ("Trap: Half Orb Spawns", 20.0),
    ("Trap: Half Collected Orbs", 20.0),
]
# (full name, weight) - effects that do not follow the standard duration split
_instant_buffs = [("Burst Orbs", 10.0)]
_special_traps = [
    ("Trap: Map Blindness (1m)", 10.0 * 0.85),
    ("Trap: Map Blindness (3m)", 10.0 * 0.15),
]


def _build_item_dictionary() -> Dict[str, ItemData]:
    """IDs are assigned sequentially in declaration order so the reserved ID block is
    exactly as large as the number of items (no gaps)."""
    items: Dict[str, ItemData] = {}

    def add(name: str, data: ItemData) -> None:
        data["id"] = TREKIPELAGO_ITEM_BASE_ID + len(items)
        items[name] = data

    for name in _progression:
        add(name, {"classification": ItemClassification.progression})

    for name, weight in _instant_buffs:
        add(name, {"classification": ItemClassification.useful, "weight_buff": weight})

    for name, weight in _timed_buffs:
        for suffix, share in _DURATION_SPLIT:
            add(
                f"{name} ({suffix})",
                {"classification": ItemClassification.useful, "weight_buff": weight * share},
            )

    for name, weight in _timed_traps:
        for suffix, share in _DURATION_SPLIT:
            add(
                f"{name} ({suffix})",
                {"classification": ItemClassification.trap, "weight_trap": weight * share},
            )

    for name, weight in _special_traps:
        add(name, {"classification": ItemClassification.trap, "weight_trap": weight})

    return items


item_dictionary: Dict[str, ItemData] = _build_item_dictionary()

_buff_pool = [(n, d["weight_buff"]) for n, d in item_dictionary.items() if "weight_buff" in d]
_trap_pool = [(n, d["weight_trap"]) for n, d in item_dictionary.items() if "weight_trap" in d]


def get_filler_item_name(rand: random.Random, buff_ratio: float = 0.7) -> str:
    pool = _buff_pool if rand.random() < buff_ratio else _trap_pool
    names = [name for name, _ in pool]
    weights = [weight for _, weight in pool]
    return rand.choices(names, weights=weights, k=1)[0]
