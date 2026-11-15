import pytest
import argparse

from pathlib import Path

from primetoolv3 import cli
from primetoolv3.core.version_manager import ReleaseInfo

def configure_cli(monkeypatch):
    calls = []

    monkeypatch.setattr(
        cli,
        "sync_release",
        lambda allow_offline: {
            "version": "1.0.1"
        },
    )

    monkeypatch.setattr(
        cli,
        "get_script_dir",
        lambda: Path("/tmp/primetoolv3/script"),
    )

    monkeypatch.setattr(
        cli,
        "create_environment",
        lambda: calls.append("create_environment"),
    )

    monkeypatch.setattr(
        cli,
        "install_dependencies",
        lambda: calls.append("install_dependencies") or True,
    )

    monkeypatch.setattr(
        cli,
        "execute_tool",
        lambda arguments: calls.append(
            ("execute_tool", arguments)
        ) or 0,
    )

    return calls


def test_handle_run_success(monkeypatch):
    calls = configure_cli(monkeypatch)

    args = argparse.Namespace(
        tool_args=["--input", "data.csv"]
    )

    result = cli.handle_run(args)

    assert result == 0
    assert calls == [
        "create_environment",
        "install_dependencies",
        ("execute_tool", ["--input", "data.csv"]),
    ]


def test_handle_run_dependency_declined(monkeypatch):
    calls = configure_cli(monkeypatch)

    monkeypatch.setattr(
        cli,
        "install_dependencies",
        lambda: False,
    )

    args = argparse.Namespace(tool_args=[])

    result = cli.handle_run(args)

    assert result == 1
    assert "execute_tool" not in calls


def test_handle_run_release_unavailable(monkeypatch):
    monkeypatch.setattr(
        cli,
        "sync_release",
        lambda allow_offline: None,
    )

    args = argparse.Namespace(tool_args=[])

    assert cli.handle_run(args) == 1


def test_handle_run_execution_failure(monkeypatch):
    configure_cli(monkeypatch)

    monkeypatch.setattr(
        cli,
        "execute_tool",
        lambda arguments: 42,
    )

    args = argparse.Namespace(tool_args=["--fail"])

    assert cli.handle_run(args) == 42


def test_handle_run_environment_error(monkeypatch):
    configure_cli(monkeypatch)

    def fail_environment():
        raise RuntimeError("Environment creation failed")

    monkeypatch.setattr(
        cli,
        "create_environment",
        fail_environment,
    )

    args = argparse.Namespace(tool_args=[])

    assert cli.handle_run(args) == 1


def test_handle_run_release_sync_error(monkeypatch):
    def fail_sync(allow_offline):
        raise RuntimeError("GitHub unavailable")

    monkeypatch.setattr(cli, "sync_release", fail_sync)

    args = argparse.Namespace(tool_args=[])

    assert cli.handle_run(args) == 1

def test_main_forwards_arguments_to_run(monkeypatch):
    captured = {}

    def fake_handle_run(args):
        captured["args"] = args
        return 0

    monkeypatch.setattr(cli, "handle_run", fake_handle_run)

    result = cli.main([
        "run",
        "--input",
        "data.csv",
        "--format",
        "parquet",
    ])

    assert result == 0
    assert captured["args"].tool_args == [
        "--input",
        "data.csv",
        "--format",
        "parquet",
    ]


def test_main_rejects_unknown_update_arguments():
    try:
        cli.main(["update", "--invalid"])
        assert False, "Expected SystemExit"
    except SystemExit as error:
        assert error.code == 2

    
def test_main_dispatches_version(monkeypatch):
    captured = {}

    def fake_handle_version(args):
        captured["called"] = True
        return 0

    monkeypatch.setattr(
        cli,
        "handle_version",
        fake_handle_version,
    )

    result = cli.main(["version"])

    assert result == 0
    assert captured["called"] is True

def test_sync_release_uses_valid_cache_when_offline(monkeypatch):
    cached = {"version": "1.0.1"}

    monkeypatch.setattr(cli, "ensure_app_dirs", lambda: None)
    monkeypatch.setattr(cli, "load_cached_release", lambda: cached)
    monkeypatch.setattr(cli, "get_script_dir", lambda: Path("/tmp/tool"))
    monkeypatch.setattr(cli, "verify_cached_assets", lambda path: True)
    monkeypatch.setattr(
        cli,
        "get_latest_release",
        lambda: (_ for _ in ()).throw(RuntimeError("Offline")),
    )

    result = cli.sync_release(allow_offline=True)

    assert result == cached


def test_sync_release_fails_offline_without_valid_cache(monkeypatch):
    monkeypatch.setattr(cli, "ensure_app_dirs", lambda: None)
    monkeypatch.setattr(cli, "load_cached_release", lambda: None)
    monkeypatch.setattr(cli, "get_script_dir", lambda: Path("/tmp/tool"))
    monkeypatch.setattr(
        cli,
        "get_latest_release",
        lambda: (_ for _ in ()).throw(RuntimeError("Offline")),
    )

    with pytest.raises(RuntimeError, match="Offline"):
        cli.sync_release(allow_offline=True)


def test_sync_release_rejects_corrupted_cache_when_offline(monkeypatch):
    cached = {"version": "1.0.1"}

    monkeypatch.setattr(cli, "ensure_app_dirs", lambda: None)
    monkeypatch.setattr(cli, "load_cached_release", lambda: cached)
    monkeypatch.setattr(cli, "get_script_dir", lambda: Path("/tmp/tool"))
    monkeypatch.setattr(cli, "verify_cached_assets", lambda path: False)
    monkeypatch.setattr(
        cli,
        "get_latest_release",
        lambda: (_ for _ in ()).throw(RuntimeError("Offline")),
    )

    with pytest.raises(RuntimeError, match="Offline"):
        cli.sync_release(allow_offline=True)

def test_sync_release_redownloads_when_cached_version_is_invalid(monkeypatch):
    invalid_cache = {"version": "not-a-version"}
    updated_cache = {"version": "1.0.2"}

    cache_results = iter([invalid_cache, updated_cache])
    downloaded = []

    remote = ReleaseInfo(
        tag_name="v1.0.2",
        version="1.0.2",
        name="Test Release",
        published_at="2026-11-15T00:00:00Z",
        html_url="https://github.com/example/repo/releases/tag/v1.0.2",
        assets={},
    )

    monkeypatch.setattr(cli, "ensure_app_dirs", lambda: None)
    monkeypatch.setattr(cli, "load_cached_release", lambda: next(cache_results))
    monkeypatch.setattr(cli, "get_script_dir", lambda: Path("/tmp/tool"))
    monkeypatch.setattr(cli, "verify_cached_assets", lambda path: True)
    monkeypatch.setattr(cli, "get_latest_release", lambda: remote)
    monkeypatch.setattr(
        cli,
        "download_release_assets",
        lambda release: downloaded.append(release),
    )
    monkeypatch.setattr(cli, "save_cached_release", lambda release: None)

    result = cli.sync_release()

    assert result == updated_cache
    assert downloaded == [remote]

def test_sync_release_keeps_newer_cached_version(monkeypatch):
    cached = {"version": "2.0.0"}
    remote = ReleaseInfo(
        tag_name="v1.9.0",
        version="1.9.0",
        name="Older Release",
        published_at="2026-11-15T00:00:00Z",
        html_url="https://github.com/example/repo/releases/tag/v1.9.0",
        assets={},
    )

    downloaded = []

    monkeypatch.setattr(cli, "ensure_app_dirs", lambda: None)
    monkeypatch.setattr(cli, "load_cached_release", lambda: cached)
    monkeypatch.setattr(cli, "get_script_dir", lambda: Path("/tmp/tool"))
    monkeypatch.setattr(cli, "verify_cached_assets", lambda path: True)
    monkeypatch.setattr(cli, "get_latest_release", lambda: remote)
    monkeypatch.setattr(
        cli,
        "download_release_assets",
        lambda release: downloaded.append(release),
    )

    result = cli.sync_release()

    assert result == cached
    assert downloaded == []
