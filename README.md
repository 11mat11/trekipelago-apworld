# Trekipelago - Archipelago Multiworld Integration

This is the custom world (`.apworld`) for **Trekipelago**, a GPS-based mobile walking game. By integrating with Archipelago, your real-world walking distance unlocks items and progression for other players in a randomized multiworld setting!

Item placement uses a light early/late split, separately for distance and orb checks:

- The first 20% can contain items that other players' worlds request through `early_items` or `local_early_items`. Those requested item names cannot be placed later in Trekipelago.
- Through 80%, other players' progression items remain eligible, subject to the normal access rules.
- Above 80%, other players' progression items are excluded; buffs, traps, and other non-progression items remain eligible unless requested early.

Percentages use the actual meter/orb thresholds, including shortened final intervals. A single check at the full target counts as 100%, not as an early check. These limits also apply to items belonging to other Trekipelago players. They complement Archipelago's reachability and balancing rules; they do not measure walking time or identify starting items that another world has not marked as early. Incompatible placement requests can make a seed impossible to generate.

Standard Archipelago options are available in the example YAML. `start_inventory` grants extra starting copies without removing items from the pool. `start_inventory_from_pool` grants starting copies and replaces matching pool items with repeatable buffs/traps according to `buff_ratio`, preserving the number of items. For example:

```yaml
start_inventory_from_pool:
  Background Tracking: 1
  Progressive Speed: 2
```

Starting with Background Tracking satisfies its early-availability requirement. Archipelago handles starting inventory delivery through its normal item protocol. `local_items`, `non_local_items`, `start_hints`, `start_location_hints`, `exclude_locations`, `priority_locations`, `accessibility`, and `progression_balancing` retain their standard meanings and still respect Trekipelago's placement rules. Hints and location restrictions should reference checks enabled by the selected distance/orb settings.
