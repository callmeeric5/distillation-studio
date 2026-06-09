from dataclasses import dataclass
from enum import Enum


class DIRECTION(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class Position:
    x: int
    y: int


OFFSETS = {
    DIRECTION.UP: (-1, 0),
    DIRECTION.DOWN: (1, 0),
    DIRECTION.LEFT: (0, -1),
    DIRECTION.RIGHT: (0, 1),
}

OPPOSITE_DIRECTIONS = {
    DIRECTION.UP: DIRECTION.DOWN,
    DIRECTION.DOWN: DIRECTION.UP,
    DIRECTION.LEFT: DIRECTION.RIGHT,
    DIRECTION.RIGHT: DIRECTION.LEFT,
}

FRIGHTEN_DURATION = 10.0


def next_position(pos: Position, direction: DIRECTION) -> Position:
    offset_x, offset_y = OFFSETS[direction]
    return Position(pos.x + offset_x, pos.y + offset_y)
