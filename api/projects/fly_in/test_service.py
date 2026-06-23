from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.projects.fly_in.service import list_maps, run_simulation


def test_list_maps_groups_known_maps() -> None:
    maps = list_maps()

    assert maps["easy"][0]["filename"] == "01_linear_path.txt"
    assert any(item["filename"] == "03_priority_puzzle.txt" for item in maps["medium"])


def test_run_simulation_linear_map_keeps_formatted_turns() -> None:
    simulation = run_simulation("easy", "01_linear_path.txt")

    assert [turn["formatted"] for turn in simulation["turns"]] == [
        "D1-waypoint1",
        "D1-waypoint2 D2-waypoint1",
        "D1-goal D2-waypoint2",
        "D2-goal",
    ]
    assert simulation["turns"][0]["moves"][0] == {
        "drone_id": 1,
        "from_zone": "start",
        "to_zone": "waypoint1",
        "duration": 1,
        "started_turn": 1,
        "arrives_turn": 2,
        "reason": "move",
    }
    assert any(wait["reason"] == "link_capacity" for wait in simulation["turns"][0]["waiting"])


def test_run_simulation_rejects_path_traversal() -> None:
    with pytest.raises(HTTPException):
        run_simulation("easy", "../README.md")


def test_run_simulation_rejects_unknown_difficulty() -> None:
    with pytest.raises(HTTPException):
        run_simulation("unknown", "01_linear_path.txt")
