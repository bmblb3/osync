from typing import cast

import yaml

from .file_pattern import FilePattern

filepatterns_type = list[dict[str, str | list[str] | bool]]


class FilePatterns(list[FilePattern]):
    @classmethod
    def from_yml(cls, file: str):
        with open(file, "r") as f:
            data = yaml.safe_load(f)  # pyright:ignore[reportAny]
        if not isinstance(data, list):
            raise ValueError(
                "The patterns YAML file must contain a list of pattern dicts"
            )
        if not all(isinstance(item, dict) for item in data):  # pyright:ignore[reportUnknownVariableType]
            raise ValueError(
                "The patterns YAML file must contain a list of pattern dicts"
            )
        return cls.from_file_patterns(cast(filepatterns_type, data))

    @classmethod
    def from_file_patterns(cls, patterns_dicts: filepatterns_type):
        items: list[FilePattern] = []
        for pdict in patterns_dicts:
            desc = cast(str, pdict["desc"])
            patterns = cast(list[str], pdict["patterns"])
            push = cast(bool, pdict["push"])
            pull = cast(bool, pdict["pull"])

            assert isinstance(desc, str)
            assert isinstance(patterns, list)
            assert isinstance(push, bool)
            assert isinstance(pull, bool)

            items.append(
                FilePattern(desc=desc, patterns=patterns, push=push, pull=pull)
            )
        return cls(items)
