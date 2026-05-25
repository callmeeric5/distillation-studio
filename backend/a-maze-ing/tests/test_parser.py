from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from src.parser import ConfigModel, Parser
from mazegen.algo.utils import GenerateMethod

# Test for validation model


@pytest.fixture
def valid_data() -> dict[str, Any]:
    return {
        "WIDTH": 10,
        "HEIGHT": 10,
        "ENTRY": "0,1",
        "EXIT": "9,9",
        "OUTPUT_FILE": "maze.txt",
        "PERFECT": True,
        "SEED": 42,
        "ALGORITHM": "backtracking",
        "DISPLAY_42": True,
    }


def test_valid_data(valid_data: dict[str, Any]) -> None:
    model = ConfigModel(**valid_data)
    assert model.width == 10
    assert model.height == 10
    assert model.entry == (1, 0)
    assert model.exit == (9, 9)
    assert model.output_file == "maze.txt"
    assert model.perfect is True
    assert model.seed == 42
    assert model.algorithm == GenerateMethod.BACKTRACKING
    assert model.display_42 is True


def test_same_entry_exit(valid_data: dict[str, Any]) -> None:
    valid_data["ENTRY"] = "0,0"
    valid_data["EXIT"] = "0,0"
    with pytest.raises(ValidationError) as info:
        ConfigModel(**valid_data)
    assert "entry and exit can't be the same!" in str(info.value)


def test_entry_exit_out_bound(valid_data: dict[str, Any]) -> None:
    valid_data["ENTRY"] = "12,2"
    valid_data["EXIT"] = "10,10"
    with pytest.raises(expected_exception=ValidationError):
        ConfigModel(**valid_data)


def test_entry_exit_rejects_edge_equal_to_dimension(
    valid_data: dict[str, Any],
) -> None:
    valid_data["ENTRY"] = "10,1"
    with pytest.raises(ValidationError) as info:
        ConfigModel(**valid_data)
    assert "entry can't be outside of the bound!" in str(info.value)


@pytest.mark.parametrize("bad_width", ["-1", "0", "1"])
def test_invalid_width(valid_data, bad_width) -> None:
    valid_data["WIDTH"] = bad_width
    with pytest.raises(ValidationError):
        ConfigModel(**valid_data)


@pytest.mark.parametrize("bad_algo", ["Unknown", 1, "ABC"])
def test_invalid_algo(valid_data, bad_algo) -> None:
    valid_data["ALGORITHM"] = bad_algo
    with pytest.raises(ValidationError):
        ConfigModel(**valid_data)


# Test for config parser


def test_valid_parser(tmp_path: Path) -> None:
    f = tmp_path / "valid_config.txt"
    content = """
# This a comment
WIDTH= 10
HEIGHT= 10
ENTRY= 0,1
EXIT= 9,9


OUTPUT_FILE= maze.txt
PERFECT= True
SEED= 42
ALGORITHM= backtracking
DISPLAY_42= True
"""
    f.write_text(content)
    parser = Parser(str(f))
    data = parser.parse()
    assert data["WIDTH"] == "10"
    assert data["SEED"] == "42"
    assert "# This a comment" not in data
    model = ConfigModel(**data)
    assert model.entry == (1, 0)
    assert model.exit == (9, 9)
    assert model.algorithm == GenerateMethod.BACKTRACKING
    assert model.display_42 is True
    assert parser.to_config() == model


def test_parser_file_not_found() -> None:
    parser = Parser("Unknown Path")
    with pytest.raises(FileNotFoundError):
        parser.parse()


def test_parser_not_text_file(tmp_path) -> None:
    f = tmp_path / "config.mp4"
    f.write_text("WIDTH=2")
    parser = Parser(str(f))
    with pytest.raises(ValueError) as info:
        parser.parse()
    assert "config file is not a .txt file!" in str(info.value)


def test_parser_bad_format(tmp_path):
    f = tmp_path / "config.txt"
    f.write_text("WIDTH: 2")
    parser = Parser(str(f))
    with pytest.raises(ValueError) as info:
        parser.parse()
    assert "expected KEY=VALUE format!" in str(info.value)
