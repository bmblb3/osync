from . import cli


def main():
    args = cli.main()
    if args.push:
        print(f"Pushing to {args.path}")
    elif args.pull:
        print(f"Pulling from {args.path}")

    if args.force:
        print("Operation will be forced.")
