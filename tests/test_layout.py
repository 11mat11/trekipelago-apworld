import pytest

from test.general import setup_multiworld
from worlds.trekipelago import TrekipelagoWorld

from .cases import LAYOUT_CASES
from .helpers import assert_layout


@pytest.mark.parametrize(
    "name,options,interval,distances,orbs,orb_interval",
    LAYOUT_CASES, ids=[case[0] for case in LAYOUT_CASES],
)
def test_layout_and_slot_data(name, options, interval, distances, orbs, orb_interval):
    multiworld = setup_multiworld(TrekipelagoWorld, seed=0, options=options)
    world = multiworld.worlds[1]
    opts = world.get_snapped_options()
    assert opts["interval"] == interval
    assert opts["distances"] == distances
    assert opts["orbs"] == orbs
    assert opts["orbs_per_reward"] == orb_interval
    assert opts["total_dist"] == options.get("total_distance", 5) * 1000
    assert opts["max_orbs"] == options.get("max_orbs", 50)
    assert_layout(multiworld, 1)


@pytest.mark.parametrize("requested,expected", [(149, 100), (150, 200), (151, 200)])
def test_distance_rounding_boundary(requested, expected):
    multiworld = setup_multiworld(TrekipelagoWorld, seed=0, options={"distance_interval": requested})
    opts = multiworld.worlds[1].get_snapped_options()
    assert opts["interval"] == expected
    assert opts["total_dist"] == 5000
    assert opts["distances"][-1] == 5000
