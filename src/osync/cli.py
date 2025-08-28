import argparse
import sys


class Args(argparse.Namespace):
    push: bool = False
    pull: bool = False
    force: bool = False
    path: str = "."


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Opinionated rsyncing to my remotes")
    group = parser.add_mutually_exclusive_group(required=True)
    _ = group.add_argument("--push", action="store_true")
    _ = group.add_argument("--pull", action="store_true")
    _ = parser.add_argument(
        "--force",
        action="store_true",
        help="Just sync this thing, don't consider the pre-configured include/exclude patterns",
    )
    _ = parser.add_argument(
        "path",
        help="The remote/local path to sync (will smartly obtain the counterpart path)",
    )
    args = parser.parse_args(argv, namespace=Args())

    return args
