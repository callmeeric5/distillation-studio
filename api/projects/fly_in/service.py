from __future__ import annotations

import re
from pathlib import Path
from typing import cast

from fastapi import HTTPException

from api.projects.fly_in.schemas import Difficulty, MapSummary
from backend.fly_in.src import Graph, ParseError, Parser, Scheduler, Solver


ROOT = Path(__file__).resolve().parents[3]
MAPS_DIR = ROOT / "backend" / "fly_in" / "maps"
DIFFICULTIES: tuple[Difficulty, ...] = ("easy", "medium", "hard", "challenger")
FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.txt$")


def list_maps() -> dict[Difficulty, list[dict]]:
    return {
        difficulty: [
            _map_summary(difficulty, path).model_dump()
            for path in sorted((MAPS_DIR / difficulty).glob("*.txt"))
        ]
        for difficulty in DIFFICULTIES
    }


def run_simulation(difficulty: str, filename: str) -> dict:
    map_path = _resolve_map_path(difficulty, filename)
    typed_difficulty = cast(Difficulty, difficulty)

    try:
        config = Parser(str(map_path)).parse()
        graph = Graph(config)
        paths = Solver(graph).solve_all()
        if not paths:
            raise HTTPException(status_code=400, detail="No valid path from start to end.")
        scheduler = Scheduler(graph, paths)
        scheduler.run()
    except ParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    formatted_turns = scheduler.formatted_turns()
    zones = []
    for zone_name, zone in graph.zones.items():
        role = "normal"
        if zone_name == graph.start:
            role = "start"
        elif zone_name == graph.end:
            role = "end"
        zones.append(
            {
                "name": zone.name,
                "position": {"x": zone.pos.x, "y": zone.pos.y},
                "zone_type": zone.zone_type.value,
                "color": zone.color,
                "max_drones": graph.zone_capacity(zone.name),
                "role": role,
            }
        )

    return {
        "map": _map_summary(typed_difficulty, map_path).model_dump(),
        "zones": zones,
        "connections": [
            {
                "source": connection.source,
                "target": connection.target,
                "max_link_capacity": connection.max_link_capacity,
            }
            for connection in graph.connections.values()
        ],
        "assignments": [
            {"drone_id": index + 1, "path": path, "path_index": index}
            for index, path in enumerate(paths)
        ],
        "turns": [
            {
                **turn,
                "formatted": formatted_turns[index] if index < len(formatted_turns) else "",
            }
            for index, turn in enumerate(scheduler.trace)
        ],
        "stats": {
            "drones": graph.nb_drones,
            "zones": len(graph.zones),
            "connections": len(graph.connections),
            "turns": len(scheduler.turns),
            "paths": len({tuple(path) for path in paths}),
            "start": graph.start,
            "end": graph.end,
        },
    }


def _resolve_map_path(difficulty: str, filename: str) -> Path:
    if difficulty not in DIFFICULTIES:
        raise HTTPException(status_code=404, detail="Unknown map difficulty.")
    if not FILENAME_RE.fullmatch(filename):
        raise HTTPException(status_code=404, detail="Unknown map file.")

    map_path = (MAPS_DIR / difficulty / filename).resolve()
    difficulty_dir = (MAPS_DIR / difficulty).resolve()
    if difficulty_dir not in map_path.parents or not map_path.is_file():
        raise HTTPException(status_code=404, detail="Unknown map file.")
    return map_path


def _map_summary(difficulty: Difficulty, path: Path) -> MapSummary:
    return MapSummary(
        difficulty=difficulty,
        filename=path.name,
        name=path.stem.replace("_", " ").title(),
        path=f"{difficulty}/{path.name}",
    )
