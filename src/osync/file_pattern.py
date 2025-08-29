from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

import yaml

FILEPATTERN_MAPPING_TYPE = Mapping[str, str | list[str] | bool]


@dataclass
class FilePattern:
    desc: str
    type: str
    patterns: list[str]
    push: bool
    pull: bool

    def rsync_args(self) -> list[str]:
        if len(self.patterns) == 0:
            raise ValueError(f"Patterns list for {self.desc} is empty")
        return [f"--include={p}" for p in self.patterns]

    @classmethod
    def from_dict(cls, in_dict: FILEPATTERN_MAPPING_TYPE):
        return cls(
            desc=cast(str, in_dict["desc"]),
            type=cast(str, in_dict["type"]),
            patterns=cast(list[str], in_dict["patterns"]),
            push=cast(bool, in_dict["push"]),
            pull=cast(bool, in_dict["pull"]),
        )


FILEPATTERNS_TYPE = Sequence[FILEPATTERN_MAPPING_TYPE]


class FilePatterns(list[FilePattern]):
    @classmethod
    def from_yml(cls, file: str):
        with open(file, "r") as f:
            data = yaml.safe_load(f)  # pyright:ignore[reportAny]
        data = cast(FILEPATTERNS_TYPE, data)
        return cls.from_file_patterns(data)

    @classmethod
    def from_file_patterns(
        cls,
        patterns_dicts: FILEPATTERNS_TYPE,
    ):
        return cls([FilePattern.from_dict(pdict) for pdict in patterns_dicts])
