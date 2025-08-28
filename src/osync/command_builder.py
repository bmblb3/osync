import os
import subprocess

from .file_pattern import FilePattern


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
        # "--exclude=.*", # exclude files matching PATTERN
        "--exclude=.git",  # exclude files matching PATTERN
        "--exclude=osync.yaml",  # exclude files matching PATTERN
        "--include=*/",  # don't exclude files matching PATTERN
    ]

    def __init__(
        self,
        push: bool,
        pull: bool,
        force: bool,
        source: str,
        dest: str,
        file_patterns: list[FilePattern],
        remote_user_host: str | None = None,
        dry_run: bool = False,
    ):
        if remote_user_host is None:
            remote_user_host = dict(os.environ).get("OSYNC_REMOTE_USER_HOST", "")
        if remote_user_host == "":
            raise ValueError(
                "Undefined or empty environment variable OSYNC_REMOTE_USER_HOST"
            )
        self.remote_user_host: str = remote_user_host
        self.push: bool = push
        self.pull: bool = pull
        self.force: bool = force
        self.file_patterns: list[FilePattern] = file_patterns

        self.args: list[str] = self.BASE_ARGS.copy()
        patterns = [
            pattern
            for pattern in self.file_patterns
            if (pattern.push if self.push else pattern.pull)
        ]

        for pattern in patterns:
            self.args.extend(pattern.rsync_args())
        if not self.force:
            self.args.extend(["--exclude=*"])

        if self.pull:
            source = self.remote_user_host + ":" + source
        if self.push:
            dest = self.remote_user_host + ":" + dest
        if dry_run:
            self.args.append("--dry-run")
        self.args.extend([source, dest])

    def execute(self) -> None:
        print(" ".join(self.args))
        result = subprocess.run(self.args)
        if result.returncode != 0:
            raise RuntimeError(f"rsync failed with code {result.returncode}")
