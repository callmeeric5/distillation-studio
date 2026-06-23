import sys

from src import Graph, ParseError, Parser, Scheduler, Solver, Visualizor


def main() -> None:
    if not len(sys.argv) == 2:
        print("usage: python main.py <map.txt>", file=sys.stderr)
        raise SystemExit(1)
    try:
        config = Parser(sys.argv[1]).parse()
        graph = Graph(config)
        paths = Solver(graph).solve_all()
        if not paths:
            print("no valid path from start to end", file=sys.stderr)
            raise SystemExit(1)
        scheduler = Scheduler(graph, paths)
        scheduler.run()
        print(f"Total turns: {len(scheduler.turns)}")
    except (ParseError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    Visualizor(graph, color=sys.stdout.isatty()).print_turns(
        scheduler.turns
    )


if __name__ == "__main__":
    main()
