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


TREKIPELAGO_ITEM_BASE_ID = 1111
# Retired IDs stay unused so existing clients keep recognizing the other items.
_RETIRED_ITEM_IDS = {1114}

# Duration variants share the base weight of their effect; the split mirrors the
# drop statistics of the mobile app.
_DURATION_SPLIT: List[Tuple[str, float]] = [("5m", 0.65), ("15m", 0.25), ("30m", 0.10)]

_PROGRESSION_ITEMS = ["Background Tracking", "Passive Collector", "Progressive Speed"]

# (effect name, base weight)
_TIMED_BUFFS = [
    ("Speed Boost", 30.0),
    ("Double Distance", 25.0),
    ("Double Orb Spawns", 25.0),
    ("Double Collected Orbs", 20.0),
]
_TIMED_TRAPS = [
    ("Trap: Slow Movement", 25.0),
    ("Trap: Half Distance", 25.0),
    ("Trap: Half Orb Spawns", 20.0),
    ("Trap: Half Collected Orbs", 20.0),
]
# (full name, weight) - effects that do not follow the standard duration split
_SPECIAL_TRAPS = [
    ("Trap: Map Blindness (1m)", 10.0 * 0.85),
    ("Trap: Map Blindness (3m)", 10.0 * 0.15),
]


def _build_item_dictionary() -> Dict[str, ItemData]:
    """Assign IDs in declaration order, preserving gaps left by retired items."""
    items: Dict[str, ItemData] = {}
    next_item_id = TREKIPELAGO_ITEM_BASE_ID

    def add_item(name: str, data: ItemData) -> None:
        nonlocal next_item_id
        while next_item_id in _RETIRED_ITEM_IDS:
            next_item_id += 1
        data["id"] = next_item_id
        items[name] = data
        next_item_id += 1

    for name in _PROGRESSION_ITEMS:
        add_item(name, {"classification": ItemClassification.progression})

    for name, weight in _TIMED_BUFFS:
        for duration, duration_share in _DURATION_SPLIT:
            add_item(
                f"{name} ({duration})",
                {
                    "classification": ItemClassification.useful,
                    "weight_buff": weight * duration_share,
                },
            )

    for name, weight in _TIMED_TRAPS:
        for duration, duration_share in _DURATION_SPLIT:
            add_item(
                f"{name} ({duration})",
                {
                    "classification": ItemClassification.trap,
                    "weight_trap": weight * duration_share,
                },
            )

    for name, weight in _SPECIAL_TRAPS:
        add_item(name, {"classification": ItemClassification.trap, "weight_trap": weight})

    return items


item_dictionary: Dict[str, ItemData] = _build_item_dictionary()

_buff_pool = [
    (item_name, item_data["weight_buff"])
    for item_name, item_data in item_dictionary.items()
    if "weight_buff" in item_data
]
_trap_pool = [
    (item_name, item_data["weight_trap"])
    for item_name, item_data in item_dictionary.items()
    if "weight_trap" in item_data
]


def get_filler_item_name(rand: random.Random, buff_ratio: float = 0.7) -> str:
    pool = _buff_pool if rand.random() < buff_ratio else _trap_pool
    names = [name for name, _ in pool]
    weights = [weight for _, weight in pool]
    return rand.choices(names, weights=weights, k=1)[0]
