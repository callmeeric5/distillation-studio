from backend.pac_man.src.maze import Cell, Maze
from backend.pac_man.src.player import Player
from backend.pac_man.src.utils import DIRECTION, Position
from pytest import approx


def test_player_buffers_turn_until_cell_center() -> None:
    player = Player(_open_maze(), lives=3, speed=5)
    player._set_position(Position(5, 5))
    player.direction = DIRECTION.RIGHT
    player.target = Position(5, 6)
    player.col = 5.8

    player.set_direction(DIRECTION.UP)
    player.on_update(0.02)

    assert player.direction == DIRECTION.RIGHT
    assert player.pos == Position(5, 5)
    assert player.target == Position(5, 6)
    assert player.col == approx(5.9)

    player.on_update(0.04)

    assert player.direction == DIRECTION.UP
    assert player.col == 6.0
    assert player.row < 5.0


def test_player_reverses_immediately_mid_cell() -> None:
    player = Player(_open_maze(), lives=3, speed=5)
    player._set_position(Position(5, 5))
    player.direction = DIRECTION.RIGHT
    player.target = Position(5, 6)
    player.col = 5.4

    player.set_direction(DIRECTION.LEFT)
    player.on_update(0.02)

    assert player.direction == DIRECTION.LEFT
    assert player.col < 5.4


def _open_maze(width: int = 10, height: int = 10) -> Maze:
    return Maze(
        width=width,
        height=height,
        cells=[
            [
                Cell(
                    north_wall=False,
                    east_wall=False,
                    south_wall=False,
                    west_wall=False,
                    is_42_pattern=False,
                )
                for _ in range(width)
            ]
            for _ in range(height)
        ],
    )
