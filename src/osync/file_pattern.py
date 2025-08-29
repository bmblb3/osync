from dataclasses import dataclass
from typing import cast

import yaml


@dataclass
class FilePattern:
    desc: str
    patterns: list[str]
    push: bool
    pull: bool

    def rsync_args(self) -> list[str]:
        if len(self.patterns) == 0:
            raise ValueError(f"Patterns list for {self.desc} is empty")
        return [f"--include={p}" for p in self.patterns]


filepatterns_type = list[dict[str, str | list[str] | bool]]


class FilePatterns(list[FilePattern]):
    @classmethod
    def from_yml(cls, file: str):
        with open(file, "r") as f:
            data = yaml.safe_load(f)  # pyright:ignore[reportAny]
        data = cast(filepatterns_type, data)
        return cls.from_file_patterns(data)

    @classmethod
    def from_file_patterns(cls, patterns_dicts: filepatterns_type):
        items = [
            FilePattern(
                desc=cast(str, pdict["desc"]),
                patterns=cast(list[str], pdict["patterns"]),
                push=cast(bool, pdict["push"]),
                pull=cast(bool, pdict["pull"]),
            )
            for pdict in patterns_dicts
        ]
        return cls(items)
