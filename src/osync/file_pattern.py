from dataclasses import dataclass


@dataclass
class FilePattern:
    desc: str
    patterns: list[str]
    push: bool = True
    pull: bool = False

    def rsync_args(self) -> list[str]:
        if len(self.patterns) == 0:
            raise ValueError(f"Patterns list for {self.desc} is empty")
        return [f"--include={p}" for p in self.patterns]
