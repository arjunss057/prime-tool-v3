import argparse
import sys

from typing import Optional

from primetoolv3 import __version__
from primetoolv3.config import APP_NAME
from primetoolv3.core.downloader import download_release_assets, verify_cached_assets
from primetoolv3.utils.paths import ensure_app_dirs, get_script_dir
from primetoolv3.core.version_manager import (
    get_latest_release,
    compare_versions,
    load_cached_release,
    save_cached_release,
    parse_version
)

def sync_release(allow_offline: bool = False) -> Optional[dict]:
    '''
    Check remote release and synchronize local cache
    If offline mode is allowed, use the last validated local release when GitHub cannot be reached
    '''

    ensure_app_dirs()
    cached = load_cached_release()
    script_dir = get_script_dir()
    cache_valid = (cached is not None) and (verify_cached_assets(script_dir))
    if cache_valid and cached is not None:
        try:
            parse_version(cached["version"])
        except (ValueError, KeyError, TypeError):
            cache_valid = False
    try:
        remote = get_latest_release()
    except RuntimeError:
        if allow_offline and cache_valid and cached is not None:
            print("Warning: Unable to connect GitHub")
            print(f"Using cached tool: {cached['version']}")
            return cached
        raise
    if not cache_valid:
        print("No valid local tool cache found")
        print(f"Downloading {remote.tag_name}...")
        download_release_assets(remote)
        save_cached_release(remote)
        print("Tool downloaded successfully")
        return load_cached_release()
    if cached is not None:
        comparison = compare_versions(remote.version, cached["version"])
        if comparison > 0:
            print(f"New tool version available: {cached['version']} -> {remote.version}")
            download_release_assets(remote)
            save_cached_release(remote)
            print("Tool updated successfully")
            return load_cached_release()
        if comparison < 0:
            print("Warning: Remote release is older than the cached version. Keeping the local version")
            return cached
        print(f"Tool is up to date: {remote.version}")
        return cached

def handle_run(args: argparse.Namespace) -> int:
    try:
        release = sync_release(allow_offline=True)
        print()
        if release is not None:
            print(f"{APP_NAME} engine: {release['versopm']}")
            print(f"Script location: {get_script_dir()/'tool.py'}")
            print()
            print("Release synchroniztion complete. Execution will be implemented later")
            return 0
        print("sync_release returned empty")
        return 1
    except (RuntimeError, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

def handle_update(args: argparse.Namespace) -> int:
    try:
        release = sync_release(allow_offline=False)
        if release is not None:
            print(f"Tool version: {release['version']}")
            return 0
        print("sync_release returned empty")
        return 1
    except (RuntimeError, OSError, ValueError) as error:
        print(f"Update failed: {error}", file=sys.stderr)
        return 1

def handle_version(args: argparse.Namespace) -> int:
    cached = load_cached_release()
    print(f"{APP_NAME} CLI: {__version__}")
    if cached:
        print(f"Tool: {cached.get('version', 'Unknown')}")
    else:
        print("Tool: Not installed")
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
    clean_parser = subparsers.add_parser("clean", help="Remove locally managed tool resources")
    clean_parser.set_defaults(func=handle_clean)

    return parser

def main(argv: Optional[list[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())