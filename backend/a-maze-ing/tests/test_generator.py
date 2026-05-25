from pathlib import Path

import numpy as np
import pytest

from mazegen.algo.utils import GenerateMethod
from mazegen.generator import MazeGenerator
from mazegen.utils import PATTERN_42, MazeGrid


def assert_wall_coherence(grid: MazeGrid) -> None:
    height, width = grid.shape
    for row in range(height):
        for col in range(width):
            if row > 0:
                assert grid.walls[row, col, 0] == grid.walls[row - 1, col, 2]
            if col < width - 1:
                assert grid.walls[row, col, 1] == grid.walls[row, col + 1, 3]
            if row < height - 1:
                assert grid.walls[row, col, 2] == grid.walls[row + 1, col, 0]
            if col > 0:
                assert grid.walls[row, col, 3] == grid.walls[row, col - 1, 1]


def test_generator_initialized() -> None:
    generator = MazeGenerator(
        width=4,
        height=3,
        entry=(0, 0),
        exit=(2, 3),
        output_file="maze.txt",
        display_42=False,
    )

    assert generator.width == 4
    assert generator.height == 3
    assert generator.output_file == "maze.txt"
    assert generator._grid.shape == (3, 4)
    assert generator._grid.walls.shape == (3, 4, 4)
    assert generator._grid.walls.dtype == np.bool_
    assert generator._grid.blocked.shape == (3, 4)
    assert not generator._grid.blocked.any()


def test_from_config(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.txt"
    config.write_text(
        "\n".join(
            [
                "WIDTH=8",
                "HEIGHT=6",
                "ENTRY=2,1",
                "EXIT=7,5",
                "OUTPUT_FILE=maze.txt",
                "PERFECT=True",
                "SEED=123",
                "ALGORITHM=binary_tree",
                "DISPLAY_42=False",
            ]
        )
    )

    generator = MazeGenerator.from_config(str(config))

    assert generator.width == 8
    assert generator.height == 6
    assert generator.entry == (1, 2)
    assert generator.exit == (5, 7)
    assert generator.output_file == "maze.txt"
    assert generator.seed == 123
    assert generator.algorithm == GenerateMethod.BINARY_TREE
    assert generator.display_42 is False


def test_generate_backtracking() -> None:
    generator = MazeGenerator(
        width=5,
        height=4,
        entry=(0, 0),
        exit=(3, 4),
        seed=7,
        display_42=False,
        output_file="",
    )

    grid = generator.generate(None)

    assert grid is generator._grid
    assert generator._visited.all()
    assert_wall_coherence(grid)


def test_generate_invaid_42_pattern() -> None:
    generator = MazeGenerator(
        width=5,
        height=4,
        entry=(0, 0),
        exit=(3, 4),
        display_42=True,
        output_file="",
    )

    with pytest.raises(ValueError, match="too small for 42 pattern"):
        generator.generate(None)


def test_generate_prim() -> None:
    trace = []
    generator = MazeGenerator(
        width=5,
        height=4,
        entry=(0, 0),
        exit=(3, 4),
        algorithm=GenerateMethod.PRIM,
        display_42=False,
        output_file="",
        trace=trace,
    )

    grid = generator.generate(None)

    assert grid is generator._grid
    assert trace
    assert_wall_coherence(grid)


def test_apply_42_pattern_blocks_expected_cells() -> None:
    generator = MazeGenerator(
        width=9,
        height=7,
        entry=(0, 0),
        exit=(6, 8),
        display_42=False,
        output_file="",
    )

    generator._apply_42_pattern()

    assert generator._grid.blocked.sum() == sum(
        cell for row in PATTERN_42 for cell in row
    )
    assert generator._grid.blocked[1, 1]
    assert generator._grid.blocked[5, 7]
