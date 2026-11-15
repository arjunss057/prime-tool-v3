import subprocess
import pytest

from primetoolv3.core import executor


def configure_executor(tmp_path, monkeypatch):
    script_dir = tmp_path / "script"
    script_dir.mkdir()

    tool_script = script_dir / "tool.py"
    tool_script.write_text(
        "print('Dummy tool')",
        encoding="utf-8",
    )

    venv_python = tmp_path / "venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.touch()

    monkeypatch.setattr(
        executor,
        "get_script_dir",
        lambda: script_dir,
    )

    monkeypatch.setattr(
        executor,
        "environment_exists",
        lambda: True,
    )

    monkeypatch.setattr(
        executor,
        "get_venv_python",
        lambda: venv_python,
    )

    return tool_script, venv_python


def test_execute_tool_success(tmp_path, monkeypatch):
    tool_script, venv_python = configure_executor(
        tmp_path, monkeypatch
    )

    captured = {}

    def fake_run(command):
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(executor.subprocess, "run", fake_run)

    result = executor.execute_tool()

    assert result == 0
    assert captured["command"] == [
        str(venv_python),
        str(tool_script),
    ]


def test_execute_tool_forwards_arguments(tmp_path, monkeypatch):
    tool_script, venv_python = configure_executor(
        tmp_path, monkeypatch
    )

    captured = {}

    def fake_run(command):
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(executor.subprocess, "run", fake_run)

    arguments = [
        "--input",
        "data.csv",
        "--format",
        "parquet",
    ]

    executor.execute_tool(arguments)

    assert captured["command"] == [
        str(venv_python),
        str(tool_script),
        *arguments,
    ]


def test_execute_tool_propagates_exit_code(tmp_path, monkeypatch):
    configure_executor(tmp_path, monkeypatch)

    def fake_run(command):
        return subprocess.CompletedProcess(command, 42)

    monkeypatch.setattr(executor.subprocess, "run", fake_run)

    assert executor.execute_tool() == 42


def test_execute_tool_missing_script(tmp_path, monkeypatch):
    script_dir = tmp_path / "script"
    script_dir.mkdir()

    monkeypatch.setattr(
        executor,
        "get_script_dir",
        lambda: script_dir,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Tool script not found",
    ):
        executor.execute_tool()


def test_execute_tool_missing_environment(tmp_path, monkeypatch):
    script_dir = tmp_path / "script"
    script_dir.mkdir()
    (script_dir / "tool.py").touch()

    monkeypatch.setattr(
        executor,
        "get_script_dir",
        lambda: script_dir,
    )

    monkeypatch.setattr(
        executor,
        "environment_exists",
        lambda: False,
    )

    with pytest.raises(
        RuntimeError,
        match="Tool environment does not exist",
    ):
        executor.execute_tool()


def test_execute_tool_os_error(tmp_path, monkeypatch):
    configure_executor(tmp_path, monkeypatch)

    def fake_run(command):
        raise OSError("Permission denied")

    monkeypatch.setattr(executor.subprocess, "run", fake_run)

    with pytest.raises(
        RuntimeError,
        match="Failed to execute tool",
    ):
        executor.execute_tool()
