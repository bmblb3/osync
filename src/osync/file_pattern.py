from dataclasses import dataclass
from typing import cast

import yaml

FILEPATTERN_DICT_TYPE = dict[str, str | list[str] | bool]


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

    @classmethod
    def from_dict(cls, in_dict: FILEPATTERN_DICT_TYPE):
        return cls(
            desc=cast(str, in_dict["desc"]),
            patterns=cast(list[str], in_dict["patterns"]),
            push=cast(bool, in_dict["push"]),
            pull=cast(bool, in_dict["pull"]),
        )


FILEPATTERNS_TYPE = list[dict[str, str | list[str] | bool]]


class FilePatterns(list[FilePattern]):
    @classmethod
    def from_yml(cls, file: str):
        with open(file, "r") as f:
            data = yaml.safe_load(f)  # pyright:ignore[reportAny]
        data = cast(FILEPATTERNS_TYPE, data)
        return cls.from_file_patterns(data)

    @classmethod
    def from_file_patterns(cls, patterns_dicts: FILEPATTERNS_TYPE):
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
