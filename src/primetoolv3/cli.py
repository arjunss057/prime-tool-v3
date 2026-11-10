import argparse
from typing import Optional

from primetoolv3 import __version__
from primetoolv3.config import APP_NAME

def handle_run(args: argparse.Namespace) -> int:
    print("Toolv3 execution is not implemented yet")
    return 2

def handle_update(args: argparse.Namespace) -> int:
    print("Toolv3 update is not implemeted yet")
    return 2

def handle_version(args: argparse.Namespace) -> int:
    print(f"{APP_NAME} CLI: {__version__}")
    print("Toolv3: Not installed")
    return 0

def handle_clean(args: argparse.Namespace) -> int:
    print("Local cleanup is not implemented yet")
    return 2

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prime-tool-v3",
        description="Manage and execute remotely maintained Python tool script"
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    # run
    run_parser = subparsers.add_parser("run", help="Prepare and execute the tool")
    run_parser.set_defaults(func=handle_run)

    # update
    update_parser = subparsers.add_parser("update", help="Download the latest tool release")
    update_parser.set_defaults(func=handle_update)

    # version
    version_parser = subparsers.add_parser("version", help="Display CLI and tool versions")
    version_parser.set_defaults(func=handle_version)

    # clean
    clean_parser = subparsers.add_parser("clean", help="Remove locally managed converter resources")
    clean_parser.set_defaults(func=handle_clean)

    return parser

def main(argv: Optional[list[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())