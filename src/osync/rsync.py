import os
import subprocess

from .filter_group import Direction, FilterGroup


class RsyncCommand:
    BASE_ARGS: list[str] = [
        "rsync",
        "--verbose",  # increase verbosity
        "--recursive",  # recurse into directories
        "--links",  # copy symlinks as symlinks
        "--copy-unsafe-links",  # only "unsafe" symlinks are transformed
        "--times",  # preserve modification times
        "--update",  # skip files that are newer on the receiver
        "--perms",  # preserve permissions
    ]

    def __init__(
        self,
        direction: Direction,
        force: bool,
        source: str,
        dest: str,
        filter_groups: list[FilterGroup],
        dry_run: bool = False,
    ):
        self.args: list[str] = self.BASE_ARGS.copy()

        if not force:
            patterns = [
                filter_group
                for filter_group in filter_groups
                if filter_group.direction == direction
            ]

            for pattern in patterns:
                self.args.extend(pattern.rsync_args())
            self.args.extend(["--exclude=*"])

        if dry_run:
            self.args.append("--dry-run")

        self.args.extend([source, dest])

    def execute(self) -> None:
        _ = subprocess.run(self.args)
