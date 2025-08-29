from enum import Enum

import yaml
from pydantic import Field, TypeAdapter, field_validator
from pydantic.dataclasses import dataclass


class Direction(Enum):
    PUSH = "push"
    PULL = "pull"


class Kind(Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"


@dataclass
class FilterGroup:
    direction: Direction
    kind: Kind
    patterns: list[str] = Field(min_length=1)

    @field_validator("direction", mode="before")
    @classmethod
    def parse_direction(cls, v: str | Direction) -> Direction:
        return v if isinstance(v, Direction) else Direction(v)

    @field_validator("kind", mode="before")
    @classmethod
    def parse_kind(cls, v: str | Kind) -> Kind:
        return v if isinstance(v, Kind) else Kind(v)

    @property
    def rsync_args(self) -> list[str]:
        return [f"--{self.kind.value}={pat}" for pat in self.patterns]


FilterGroupList = TypeAdapter(list[FilterGroup])


def load_filter_groups(path: str) -> list[FilterGroup]:
    with open(path) as f:
        raw = yaml.safe_load(f)  # pyright:ignore[reportAny]
    return FilterGroupList.validate_python(raw)
