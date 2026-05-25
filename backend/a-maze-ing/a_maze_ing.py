import sys

from mazegen.generator import MazeGenerator
from mazegen.solver import MazeSolver


def main() -> None:
    """
    The main function that will create and handle
    all the a_maze_ing
    """
    if len(sys.argv) != 2:
        return
    path = sys.argv[1].strip()
    try:
        maze_generator = MazeGenerator.from_config(path)
        grid = maze_generator.generate(None)
        maze_generator.print_maze()
        maze_solver = MazeSolver(
            grid, maze_generator.entry, maze_generator.exit
        )
        maze_solver.save(None, maze_generator.output_file)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
