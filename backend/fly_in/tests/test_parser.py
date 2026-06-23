import pytest

from src import ParseError, Parser


def test_parser_file_not_found() -> None:
    parser = Parser("Unknown Path")
    with pytest.raises(ParseError):
        parser.parse()


def test_not_txt_file(tmp_path) -> None:
    f = tmp_path / "config.mp4"
    f.write_text("WIDTH=2")
    parser = Parser(str(f))
    with pytest.raises(ParseError):
        parser.parse()


def test_duplicated_start(tmp_path) -> None:
    f = tmp_path / "test.txt"
    f.write_text(
        "\n".join(
            [
                "# Easy Level 1: Simple linear path",
                "nb_drones: 2",
                "start_hub: start 0 0 [color=green]",
                "start_hub: start 0 0 [color=green]",
                "hub: waypoint1 1 0 [color=blue]",
                "end_hub: goal 3 0 [color=red]",
            ]
        )
    )
    parser = Parser(str(f))
    with pytest.raises(ParseError):
        parser.parse()


def test_duplicated_end(tmp_path) -> None:
    f = tmp_path / "test.txt"
    f.write_text(
        "\n".join(
            [
                "# Easy Level 1: Simple linear path",
                "nb_drones: 2",
                "start_hub: start 0 0 [color=green]",
                "end_hub: goal 0 0 [color=green]",
                "end_hub: goal 3 0 [color=red]",
                "hub: waypoint1 1 0 [color=blue]",
            ]
        )
    )
    parser = Parser(str(f))
    with pytest.raises(ParseError):
        parser.parse()


def test_unknow_key(tmp_path) -> None:
    f = tmp_path / "test.txt"
    f.write_text(
        "\n".join(
            [
                "# Easy Level 1: Simple linear path",
                "nb_drones: 2",
                "start_hub: start 0 0 [color=green]",
                "test_hub: waypoint3 0 0",
                "end_hub: goal 3 0 [color=red]",
                "hub: waypoint1 1 0 [color=blue]",
            ]
        )
    )
    parser = Parser(str(f))
    with pytest.raises(ParseError):
        parser.parse()


def test_invalid_nb_drones(tmp_path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("nb_drones: 0")
    parser = Parser(str(f))
    with pytest.raises(ParseError):
        parser.parse()


def test_invalid_zone(tmp_path) -> None:
    f = tmp_path / "test.txt"
    f.write_text(
        "\n".join(
            [
                "# Easy Level 1: Simple linear path",
                "nb_drones: 2",
                "start_hub: start 0 0 [color=green]",
                "end_hub: goal 3 0 [color=red]",
                "hub: bottleneck-1-0 [color=orange max_drones=2]",
            ]
        )
    )
    parser = Parser(str(f))
    with pytest.raises(ParseError):
        parser.parse()


def test_invalid_connection(tmp_path) -> None:
    f = tmp_path / "test.txt"
    f.write_text(
        "\n".join(
            [
                "# Easy Level 1: Simple linear path",
                "nb_drones: 2",
                "start_hub: start 0 0 [color=green]",
                "end_hub: goal 3 0 [color=red]",
                "connection: start-waypoint1 [color=orange max_drones=2]",
            ]
        )
    )
    parser = Parser(str(f))
    with pytest.raises(ParseError):
        parser.parse()
