from src import Graph, Parser, Scheduler, Solver


def test_scheduler_linear_output() -> None:
    config = Parser("maps/easy/01_linear_path.txt").parse()
    graph = Graph(config)
    paths = Solver(graph).solve_all()
    scheduler = Scheduler(graph, paths)

    scheduler.run()

    assert scheduler.formatted_turns() == [
        "D1-waypoint1",
        "D1-waypoint2 D2-waypoint1",
        "D1-goal D2-waypoint2",
        "D2-goal",
    ]


def test_scheduler_respects_zone_capacity() -> None:
    config = Parser("maps/easy/03_basic_capacity.txt").parse()
    graph = Graph(config)
    paths = Solver(graph).solve_all()
    scheduler = Scheduler(graph, paths)

    scheduler.run()

    assert len(scheduler.formatted_turns()) == 6
