from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


GenerateAlgorithm = Literal["backtracking", "binary_tree", "sidewinder", "prim"]
SolveAlgorithm = Literal["astar", "bfs", "dfs"]
MazeTheme = Literal["classic", "midnight", "forest", "ember"]


class Coord(BaseModel):
    row: int = Field(..., ge=0)
    col: int = Field(..., ge=0)


class MazeRequest(BaseModel):
    width: int = Field(21, ge=5, le=50)
    height: int = Field(15, ge=5, le=40)
    entry: Coord = Field(default_factory=lambda: Coord(row=0, col=0))
    exit: Coord = Field(default_factory=lambda: Coord(row=14, col=20))
    display_42: bool = False
    perfect: bool = True
    seed: int = Field(42, ge=0, le=999999)
    generate_algorithm: GenerateAlgorithm = "backtracking"
    solve_algorithm: SolveAlgorithm = "astar"
    theme: MazeTheme = "classic"
