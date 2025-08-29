from . import cli
from .filter_group import Direction, load_filter_groups
from .findup import findup
from .path_resolver import PathResolver
from .rsync import RsyncCommand


def main():
    args = cli.main()

    pattern_config = findup("osync.yaml")

    filter_groups = load_filter_groups(pattern_config)

    path_resolver = PathResolver()
    if args.push:
        source = path_resolver.to_local(args.path)
        dest = path_resolver.to_remote(args.path)
    else:
        source = path_resolver.to_remote(args.path)
        dest = path_resolver.to_local(args.path)

    direction = Direction.PUSH if args.push else Direction.PULL

    command = RsyncCommand(
        direction=direction,
        source=source,
        dest="/".join(dest.split("/")[:-1]) + "/.",
        filter_groups=filter_groups,
        force=args.force,
        dry_run=args.dry_run,
    )
    command.build()
    command.execute()
