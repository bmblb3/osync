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
        # "--exclude=.git*",  # exclude files matching PATTERN
        "--include=*/",  # don't exclude files matching PATTERN
    ]

    def __init__(
        self, push: bool, pull: bool, force: bool, file_patterns: list[FilePattern]
    ):
        self.push: bool = push
        self.pull: bool = pull
        self.force: bool = force
        self.file_patterns: list[FilePattern] = file_patterns

    def build(self, source: str, dest: str) -> list[str]:
        patterns = [
            pattern
            for pattern in self.file_patterns
            if (pattern.push if self.push else pattern.pull)
        ]

        args = self.BASE_ARGS.copy()
        for pattern in patterns:
            args.extend(pattern.rsync_args())
        if not self.force:
            args.extend(["--exclude=*"])

        args.extend([source, dest])
        return args

    def execute(self, args: list[str]) -> None:
        print(" ".join(args))
        result = subprocess.run(args)
        if result.returncode != 0:
            raise RuntimeError(f"rsync failed with code {result.returncode}")
