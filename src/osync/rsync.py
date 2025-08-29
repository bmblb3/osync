import os
import subprocess
from dataclasses import dataclass, field

from .filter_group import Direction, FilterGroup


@dataclass
class RsyncCommand:
    direction: Direction
    source: str
    dest: str
    filter_groups: list[FilterGroup]
    force: bool = False
    dry_run: bool = False
    base_args: list[str] = field(
        default_factory=lambda: [
            "rsync",
            "--verbose",  # increase verbosity
            "--recursive",  # recurse into directories
            "--links",  # copy symlinks as symlinks
            "--copy-unsafe-links",  # only "unsafe" symlinks are transformed
            "--times",  # preserve modification times
            "--update",  # skip files that are newer on the receiver
            "--perms",  # preserve permissions
        ]
    )
    args: list[str] = field(default_factory=lambda: [])

    def build(self):
        self.args = self.base_args.copy()

        if not self.force:
            self.args += [
                arg
                for filter_group in self.filter_groups
                for arg in filter_group.rsync_args
                if filter_group.direction == self.direction
            ] + ["--exclude=*"]

        if self.dry_run:
            self.args += ["--dry-run"]

        self.args += [self.source, self.dest]

    def execute(self) -> None:
        _ = subprocess.run(self.args)
