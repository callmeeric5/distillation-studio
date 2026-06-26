from backend.pac_man.src.ghost import Ghost, GhostState
from backend.pac_man.src.level import Level
from backend.pac_man.src.maze import Cell, Maze
from backend.pac_man.src.parser import Config, LevelConfig
from backend.pac_man.src.player import Player
from backend.pac_man.src.utils import DIRECTION, Position


def test_path_crossing_chase_ghost_costs_a_life() -> None:
    level = _level()
    level.player.lives = 1
    ghost = level.ghosts[0]
    ghost._set_position(Position(5, 6))

    level._check_ghost_collision(
        player_path=((5.0, 5.0), (5.0, 6.0)),
        ghost_paths=[((5.0, 6.0), (5.0, 5.0))],
    )

    assert level.player.lives == 0
    assert level.game_over is True


def test_path_crossing_frightened_ghost_is_eaten() -> None:
    level = _level()
    ghost = level.ghosts[0]
    ghost._set_position(Position(5, 6))
    ghost.direction = DIRECTION.LEFT
    ghost.get_frightened()

    level._check_ghost_collision(
        player_path=((5.0, 5.0), (5.0, 6.0)),
        ghost_paths=[((5.0, 6.0), (5.0, 5.0))],
    )

    assert level.player.lives == 3
    assert level.player.score == level.config.points_per_ghost
    assert ghost.state == GhostState.EATEN
    assert level.game_over is False


def _level() -> Level:
    maze = _open_maze()
    level = Level.__new__(Level)
    level.config = Config(levels=[LevelConfig(width=10, height=10, seed=1) for _ in range(10)])
    level.is_cheat_mode = False
    level.lvl = 0
    level.maze = maze
    level.player = Player(maze, lives=3, speed=5)
    level.player._set_position(Position(5, 5))
    level.ghosts = [Ghost(maze, Position(5, 6), speed=4)]
    level.super_pacgums = []
    level.pacgums = []
    level.time_left = 90.0
    level.win = False
    level.game_over = False
    return level


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
