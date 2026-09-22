import random
from typing import Dict, TypedDict

from BaseClasses import Item, ItemClassification

class TrekipelagoItem(Item):
    game = "Trekipelago"


class ItemData(TypedDict, total=False):
    id: int
    classification: ItemClassification
    weight_buff: float
    weight_trap: float


TREKIPELAGO_ITEM_BASE_ID = 890000000

item_dictionary: Dict[str, ItemData] = {
    # 1. Main progression
    "Background Tracking": {
        "id": TREKIPELAGO_ITEM_BASE_ID + 0,
        "classification": ItemClassification.progression,
    },
    "Passive Collector": {
        "id": TREKIPELAGO_ITEM_BASE_ID + 1,
        "classification": ItemClassification.progression,
    },
    "Progressive Speed": {
        "id": TREKIPELAGO_ITEM_BASE_ID + 2,
        "classification": ItemClassification.progression,
    },
    # 2. Buffs (Useful) - instant / stateless
    "Burst Orbs": {
        "id": TREKIPELAGO_ITEM_BASE_ID + 12,
        "classification": ItemClassification.useful,
        "weight_buff": 10.0,
    },
}

_base_buffs = [
    ("Speed Boost", 3, 30.0),
    ("Double Distance", 4, 25.0),
    ("Double Orb Spawns", 5, 25.0),
    ("Double Collected Orbs", 6, 20.0),
]

_base_traps = [
    ("Trap: Slow Movement", 7, 25.0),
    ("Trap: Half Distance", 8, 25.0),
    ("Trap: Half Orb Spawns", 9, 20.0),
    ("Trap: Half Collected Orbs", 10, 20.0),
]

# Add duration variants (5m, 15m, 30m) using weights from the mobile app
for name, base_offset, weight in _base_buffs:
    item_dictionary[f"{name} (5m)"] = {
        "id": TREKIPELAGO_ITEM_BASE_ID + base_offset * 10,
        "classification": ItemClassification.useful,
        "weight_buff": weight * 0.65,
    }
    item_dictionary[f"{name} (15m)"] = {
        "id": TREKIPELAGO_ITEM_BASE_ID + base_offset * 10 + 1,
        "classification": ItemClassification.useful,
        "weight_buff": weight * 0.25,
    }
    item_dictionary[f"{name} (30m)"] = {
        "id": TREKIPELAGO_ITEM_BASE_ID + base_offset * 10 + 2,
        "classification": ItemClassification.useful,
        "weight_buff": weight * 0.10,
    }

for name, base_offset, weight in _base_traps:
    item_dictionary[f"{name} (5m)"] = {
        "id": TREKIPELAGO_ITEM_BASE_ID + base_offset * 10,
        "classification": ItemClassification.trap,
        "weight_trap": weight * 0.65,
    }
    item_dictionary[f"{name} (15m)"] = {
        "id": TREKIPELAGO_ITEM_BASE_ID + base_offset * 10 + 1,
        "classification": ItemClassification.trap,
        "weight_trap": weight * 0.25,
    }
    item_dictionary[f"{name} (30m)"] = {
        "id": TREKIPELAGO_ITEM_BASE_ID + base_offset * 10 + 2,
        "classification": ItemClassification.trap,
        "weight_trap": weight * 0.10,
    }

# Special traps with custom duration weights (1m and 3m)
item_dictionary["Trap: Map Blindness (1m)"] = {
    "id": TREKIPELAGO_ITEM_BASE_ID + 110,
    "classification": ItemClassification.trap,
    "weight_trap": 10.0 * 0.85,
}
item_dictionary["Trap: Map Blindness (3m)"] = {
    "id": TREKIPELAGO_ITEM_BASE_ID + 111,
    "classification": ItemClassification.trap,
    "weight_trap": 10.0 * 0.15,
}


def get_filler_item_name(rand: random.Random, buff_ratio: float = 0.7) -> str:
    is_buff = rand.random() < buff_ratio

    candidates = []
    for name, data in item_dictionary.items():
        if is_buff and "weight_buff" in data:
            candidates.append((name, data["weight_buff"]))
        elif not is_buff and "weight_trap" in data:
            candidates.append((name, data["weight_trap"]))

    if not candidates:
        return "Speed Boost (5m)"  # Safe fallback
    if not candidates:
        return "Speed Boost (5m)" # Safe fallback

    total_weight = sum(weight for name, weight in candidates)
    roll = rand.random() * total_weight

    for name, weight in candidates:
        if roll <= weight:
            return name
        roll -= weight

    return candidates[0][0]
