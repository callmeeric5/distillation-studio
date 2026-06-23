from .graph import Graph


ANSI_COLORS = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "purple": "35",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "gray": "90",
    "grey": "90",
    "orange": "33",
    "gold": "33",
    "lime": "92",
}


class Visualizor:
    """Print simulation turns with optional terminal colors."""

    def __init__(self, graph: Graph, color: bool = True) -> None:
        self.graph = graph
        self.color = color

    def print_turns(self, turns: list[list[str]]) -> None:
        for turn in turns:
            print(" ".join(self._format_move(move) for move in turn))

    def _format_move(self, move: str) -> str:
        if not self.color:
            return move

        _, zone_name = move.split("-", 1)
        color_name = self.graph.get_zone(zone_name).color
        if color_name is None:
            return move

        code = ANSI_COLORS.get(color_name.lower())
        if code is None:
            return move
        return f"\033[{code}m{move}\033[0m"
