from . import cli
from .command_builder import RsyncCommand
from .file_patterns_builder import FilePatterns
from .findup import findup
from .path_resolver import PathResolver


def main():
    args = cli.main()
    pattern_config = findup("osync.yaml")
    file_patterns = FilePatterns.from_yml(pattern_config)

    path_resolver = PathResolver()
    if args.push:
        source = path_resolver.to_local(args.path)
        dest = path_resolver.to_remote(args.path)
    else:
        source = path_resolver.to_remote(args.path)
        dest = path_resolver.to_local(args.path)
    RsyncCommand(
        push=args.push,
        pull=args.pull,
        force=args.force,
        file_patterns=file_patterns,
        source=source.as_posix(),
        dest=dest.parent.as_posix() + "/.",
    ).execute()
