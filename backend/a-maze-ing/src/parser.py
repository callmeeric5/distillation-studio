from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from mazegen.algo.utils import GenerateMethod


class ConfigModel(BaseModel):
    '''
        The pydantic pipline

        Validate and Serialize the data in an understandable way
        with the use of Field validator and alias

        Attributes:
            width:       With the key alias WIDTH is the width of the
                         maze as an int and must be greater than 2
            height:      With the key alias HEIGHT is the height of the
                         maze as an int and must be greater than 2
            entry:       With the key alias ENTRY is the coord of the
                         maze entry as an int tuple
            exit:        With the key alias EXIT is the coord of the
                         maze exit as an int tuple
            output_file: With the key alias OUTPUT_FILE is the path of
                         the output file as a string
            perfect:     With the key alias PERFECT is a boolean to make
                         the maze perfect or not
            seed:        With the key alias SEED is the seed of the maze as an
                         int by default it is 42 and must be greater than 0
            algorithm:   With the key alias ALGORITHM is the algorithm that
                         must be used by default it is backtracking
            display_42:  With the key alias DISPLAY_42 is a boolean to
                         choos if the 42 pattern is shown
    '''
    width: int = Field(..., alias="WIDTH", gt=2)
    height: int = Field(..., alias="HEIGHT", gt=2)
    entry: tuple[int, int] = Field(..., alias="ENTRY")
    exit: tuple[int, int] = Field(..., alias="EXIT")
    output_file: str = Field(..., alias="OUTPUT_FILE")
    perfect: bool = Field(..., alias="PERFECT")
    seed: int = Field(default=42, alias="SEED", ge=0)
    algorithm: GenerateMethod = Field(
        default=GenerateMethod.BACKTRACKING, alias="ALGORITHM"
    )
    display_42: bool = Field(default=True, alias="DISPLAY_42")

    @field_validator("entry", "exit", mode="before")
    def parse_coord(cls, coord: str | tuple[int, int]) -> tuple[int, int]:
        '''
            Convert the entry and exit in int tuple if they are string

            Args:
                coord: Coordinate as an int tuple of a string

            Returns:
                A tuple of int representing row and colum

            Raises:
                ValueError: if it's a string that is not in the "X,Y"
                            format AND if it isn't positive value
        '''
        if isinstance(coord, tuple):
            return coord
        if isinstance(coord, str):
            parts = coord.split(",")
            if len(parts) == 2:
                x_str, y_str = (part.strip() for part in parts)
            else:
                raise ValueError("coordinate must be x,y")
            if x_str.isdigit() and y_str.isdigit():
                x, y = int(x_str), int(y_str)
                return (y, x)
        raise ValueError("coordinate must be x,y")

    @model_validator(mode="after")
    def validate_coord(self) -> Self:
        '''
            Check the global consistance of the data

            Check if the entry and exit are equal and in bounds

            Returns:
                The instance of ConfigModel

            Raises:
                ValueError if the entry and exit share the same cells
                or are not in bounds
        '''
        def _in_bounds(coord: tuple[int, int]) -> bool:
            row, col = coord
            return 0 <= row < self.height and 0 <= col < self.width

        if self.entry == self.exit:
            raise ValueError("entry and exit can't be the same!")
        if not _in_bounds(self.entry):
            raise ValueError("entry can't be outside of the bound!")
        if not _in_bounds(self.exit):
            raise ValueError("exit can't be outside of the bound!")

        return self


class Parser:
    '''
        The parsing class for the given file's path

        Attributes:
            path: the path to the config file as a str
    '''
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def parse(self) -> dict[str, Any]:
        '''
            Parse the config file to create a dictionary

            Parse the whole config file, ignore the comment (#)
            and check if everythin is to the key value format

            Returns:
                A dictionary with the parsed key and
                value as strings

            Raises:
                FileNotFoundError: If the file does not exist
                ValueError: If the file isn't a .txt OR a value
                            is not on the KEY=VALUE format
        '''
        if not self.path.is_file():
            raise FileNotFoundError
        if not self.path.suffix == ".txt":
            raise ValueError("config file is not a .txt file!")
        data = {}
        lines = self.path.read_text().splitlines()
        for lineno, line in enumerate(lines, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition("=")
            if not sep:
                raise ValueError(f"{lineno}: expected KEY=VALUE format!")
            data[key.strip()] = value.strip()
        return data

    def to_config(self) -> ConfigModel:
        '''
            Call the method and class above to make a clean
            and validated data moldel

            Returns:
                A validated model with the ConfigModel
        '''
        data = self.parse()
        return ConfigModel(**data)
