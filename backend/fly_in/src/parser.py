import re
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ParseError(Exception):
    pass


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Position(BaseModel):
    x: int
    y: int


class Zone(BaseModel):
    name: str
    pos: Position
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = Field(default=1, ge=1)


class Connection(BaseModel):
    source: str
    target: str
    max_link_capacity: int = Field(default=1, ge=1)


class Config(BaseModel):
    nb_drones: int = Field(default=1, ge=1)
    start: Zone | None = None
    end: Zone | None = None
    zones: list[Zone] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)


class Parser:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.config = Config()

    def parse(self) -> Config:
        if not self.path.exists():
            raise ParseError("file not found")

        if self.path.suffix != ".txt":
            raise ParseError("a valid file must be .txt")

        with self.path.open("r", encoding="utf-8") as file:
            for lineno, raw_line in enumerate(file, start=1):
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                if line.startswith("nb_drones"):
                    self.config.nb_drones = self._parse_nb_drones(lineno, line)

                elif line.startswith("start_hub"):
                    if self.config.start is not None:
                        raise ParseError(
                            f"line {lineno}: duplicated start hub"
                        )
                    self.config.start = self._parse_zone(lineno, line)
                elif line.startswith("hub"):
                    self.config.zones.append(self._parse_zone(lineno, line))
                elif line.startswith("end_hub"):
                    if self.config.end is not None:
                        raise ParseError(f"line {lineno}: duplicated end hub")
                    self.config.end = self._parse_zone(lineno, line)
                elif line.startswith("connection"):
                    self.config.connections.append(
                        self._parse_connection(lineno, line)
                    )
                else:
                    raise ParseError(f"line {lineno}: unknown key")
        self._validate_config()
        return self.config

    def _parse_nb_drones(self, lineno: int, line: str) -> int:
        key, sep, value = line.partition(":")

        if sep != ":":
            raise ParseError(f"line {lineno}: expected KEY: VALUE format!")

        if key.strip() != "nb_drones":
            raise ParseError(f"line {lineno}: expected nb_drones!")

        try:
            nb_drones = int(value.strip())

        except ValueError:
            raise ParseError(
                f"line {lineno}: {value.strip()} is not a valid number!"
            )
        if nb_drones < 1:
            raise ParseError(f"line {lineno}: nb_drones must be >= 1!")
        return nb_drones

    def _parse_zone(self, lineno: int, line: str) -> Zone:
        key, sep, value = line.partition(":")

        if sep != ":":
            raise ParseError(f"line {lineno}: expected KEY: VALUE format!")

        meta_data: dict[str, str] = {}
        match = re.search(r"\[(.*?)\]", value)

        if match:
            meta = match.group(1)
            meta_data = dict(re.findall(r"(\w+)=([^\s]+)", meta))
            value = re.sub(r"\[.*?\]", "", value)
        entities = value.strip().split()
        if len(entities) != 3:
            raise ParseError(
                f"line {lineno}: expected '<name> <x> <y> [metadata]'!"
            )

        name, x_raw, y_raw = entities
        if "-" in name or " " in name:
            raise ParseError(
                f"line {lineno}: zone name cannot contain '-' or spaces!"
            )
        try:
            x = int(x_raw)
            y = int(y_raw)
        except ValueError:
            raise ParseError(
                f"line {lineno}: {entities[1].strip()} "
                "{entities[2].strip()} is not a valid number!"
            )
        allowed_keys = set(["max_drones", "zone", "color"])
        if set(meta_data.keys()) - allowed_keys:
            raise ParseError(f"line {lineno}: unknown metadata keys exisits")
        try:
            max_drones = int(meta_data.get("max_drones", 1))
        except ValueError:
            raise ParseError(
                f"line {lineno}: {meta_data.get('max_drones', 1)}"
                " is not a valid number!"
            )
        return Zone(
            name=name,
            pos=Position(x=x, y=y),
            zone_type=ZoneType(meta_data.get("zone", ZoneType.NORMAL.value)),
            color=meta_data.get("color", None),
            max_drones=max_drones,
        )

    def _parse_connection(self, lineno: int, line: str) -> Connection:
        key, sep, value = line.partition(":")

        if sep != ":":
            raise ParseError(f"line {lineno}: expected KEY: VALUE format!")

        if key.strip() != "connection":
            raise ParseError(f"line {lineno}: expected connection!")

        meta_data: dict[str, str] = {}

        match = re.search(r"\[(.*?)\]", value)
        if match:
            meta = match.group(1)
            meta_data = dict(re.findall(r"(\w+)=([^\s]+)", meta))
            value = re.sub(r"\[.*?\]", "", value)

        entities = value.strip().split("-")

        if len(entities) != 2:
            raise ParseError(
                f"line {lineno}: expected '<zone>-<zone> [metadata]'!"
            )
        allowed_keys = set(["max_link_capacity"])
        if set(meta_data.keys()) - allowed_keys:
            raise ParseError(f"line {lineno}: unknown metadata keys exisits")
        source, target = entities
        source = source.strip()
        target = target.strip()
        if not source or not target:
            raise ParseError(
                f"line {lineno}: connection endpoints cannot be empty!"
            )
        try:
            max_link_capacity = int(meta_data.get("max_link_capacity", "1"))
        except ValueError as exc:
            raise ParseError(
                f"line {lineno}: max_link_capacity must be a valid integer!"
            ) from exc

        return Connection(
            source=source,
            target=target,
            max_link_capacity=max_link_capacity,
        )

    def _validate_config(self) -> None:
        if self.config.start is None:
            raise ParseError("missing start_hub")

        if self.config.end is None:
            raise ParseError("missing end_hub")
        names = [self.config.start.name]
        names.append(self.config.end.name)
        names.extend([zone.name for zone in self.config.zones])
        if not len(names) == len(set(names)):
            raise ParseError("duplicated name exists!")
        seen = set()
        for connection in self.config.connections:
            if connection.source not in names:
                raise ParseError(f"unknown name of {connection.source}!")
            if connection.target not in names:
                raise ParseError(f"unknown name of {connection.target}!")
            zone_pack = tuple(sorted((connection.source, connection.target)))
            if zone_pack in seen:
                raise ParseError(
                    f"duplicated connection: \
                        {(connection.source, connection.target)} exists!"
                )
            seen.add(zone_pack)
