import json
from pathlib import Path
from typing import Any, Self

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from backend.pac_man.src.logger import logger


class LevelConfig(BaseModel):
    """Configuration for one maze level.

    Attributes:
        width: Width of the generated maze.
        height: Height of the generated maze.
        seed: Optional random seed used to generate the maze.
    """

    width: int = Field(default=20, ge=10, le=99)
    height: int = Field(default=20, ge=10, le=99)
    seed: int | None = Field(default=None)


class Config(BaseModel):
    """Game configuration loaded from a JSON config file.

    Attributes:
        levels: Level definitions used by the game.
        level_max_time: Maximum duration of each level in seconds.
        lives: Number of lives available to the player.
        pacgum: Number of pacgums placed in a level.
        points_per_pacgum: Score awarded for one pacgum.
        points_per_super_pacgum: Score awarded for one super pacgum.
        points_per_ghost: Score awarded for one ghost.
        highscore_filename: JSON file used to store the high score.
        window_width: Width of the game window in pixels.
        window_height: Height of the game window in pixels.
        fps: Target frames per second.
    """

    levels: list[LevelConfig] = Field(
        default_factory=lambda: [LevelConfig() for _ in range(10)],
        min_length=10,
    )
    level_max_time: int = Field(default=90, ge=10)
    lives: int = Field(default=3, ge=1, le=99)
    pacgum: int = Field(default=42, ge=1, le=999)
    points_per_pacgum: int = Field(default=10, ge=1, le=999)
    points_per_super_pacgum: int = Field(default=50, ge=1, le=999)
    points_per_ghost: int = Field(default=200, ge=1, le=999)
    highscore_filename: str = Field(default="highscore.json")
    window_width: int = Field(default=1280, ge=640)
    window_height: int = Field(default=720, ge=480)
    fps: int = Field(default=60, ge=30, le=240)

    @field_validator("highscore_filename", mode="before")
    @classmethod
    def validate_highscore(cls, highscore_filename: str) -> str:
        if Path(highscore_filename).suffix != ".json":
            raise ValueError("highscore file must be json")
        return highscore_filename

    @model_validator(mode="after")
    def validate_points(self) -> Self:
        if not (
            self.points_per_pacgum
            < self.points_per_super_pacgum
            < self.points_per_ghost
        ):
            raise ValueError(
                "points should follow pacgum < super pacgum < ghost"
            )
        return self


class Parser:
    """Load and validate game configuration from a JSON file."""

    def __init__(self, path: str) -> None:
        """Store the path to the configuration file.

        Args:
            path: Path to the JSON configuration file.
        """
        self.path = Path(path)

    def load(self) -> Config:
        """Load the configuration file.

        Returns:
            A validated config, or the default config when the file cannot be
            loaded or parsed.
        """
        if not self.path.is_file():
            logger.warning("config is not a file")
            return Config()
        if not self.path.suffix == ".json":
            logger.warning("config is not a valid json")
            return Config()
        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                return self._validate(data)
        except Exception as e:
            logger.warning(f"failed to read config, {e}")
            return Config()

    def _validate(self, data: dict[str, Any]) -> Config:
        """Validate raw configuration data.

        Args:
            data: Raw configuration values loaded from JSON.

        Returns:
            A validated config with invalid fields replaced by defaults.
        """
        try:
            unknown_keys = set(data.keys()) - set(Config.model_fields.keys())
            for unknown_key in unknown_keys:
                logger.info(f"skip {unknown_key}")
            return Config.model_validate(data)
        except ValidationError as e:
            defaults = Config()
            data_copy = data.copy()
            for err in e.errors():
                key = str(err["loc"][0])
                data_copy[key] = getattr(defaults, key)
                logger.warning(
                    f"Invalid config field {key}, using default "
                    f"value: {getattr(defaults, key)}",
                )

        return Config.model_validate(data_copy)
