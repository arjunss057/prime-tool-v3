
import json
import subprocess
from types import SimpleNamespace

import pytest

from primetoolv3.core import dependency_manager as manager


def configure_test_paths(tmp_path, monkeypatch):
    requirements_file = tmp_path / "requirements.txt"
    state_file = tmp_path / "metadata" / "dependencies.json"

    monkeypatch.setattr(
        manager,
        "get_requirements_file",
        lambda: requirements_file,
    )

    monkeypatch.setattr(
        manager,
        "get_dependency_state_file",
        lambda: state_file,
    )

    monkeypatch.setattr(
        manager,
        "environment_exists",
        lambda: True,
    )

    monkeypatch.setattr(
        manager,
        "get_venv_python",
        lambda: tmp_path / "venv" / "bin" / "python",
    )

    return requirements_file, state_file


def test_calculate_requirements_hash(tmp_path, monkeypatch):
    requirements_file, _ = configure_test_paths(
        tmp_path, monkeypatch
    )

    requirements_file.write_text(
        "requests==2.32.3\n",
        encoding="utf-8",
    )

    first_hash = manager.calculate_requirements_hash()

    requirements_file.write_text(
        "requests==2.32.3\npandas==2.2.3\n",
        encoding="utf-8",
    )

    second_hash = manager.calculate_requirements_hash()

    assert first_hash != second_hash


def test_empty_requirements(tmp_path, monkeypatch):
    requirements_file, state_file = configure_test_paths(
        tmp_path, monkeypatch
    )

    requirements_file.write_text(
        "# No third-party dependencies required.\n",
        encoding="utf-8",
    )

    result = manager.install_dependencies()

    assert result is True
    assert state_file.is_file()

    with state_file.open(encoding="utf-8") as file:
        state = json.load(file)

    assert state["requirements_hash"] == (
        manager.calculate_requirements_hash()
    )


def test_dependencies_already_current(tmp_path, monkeypatch):
    requirements_file, state_file = configure_test_paths(
        tmp_path, monkeypatch
    )

    requirements_file.write_text(
        "requests==2.32.3\n",
        encoding="utf-8",
    )

    state_file.parent.mkdir(parents=True)

    manager.save_dependency_state(
        manager.calculate_requirements_hash()
    )

    def unexpected_run(*args, **kwargs):
        raise AssertionError("Dependencies should not be reinstalled")

    monkeypatch.setattr(manager.subprocess, "run", unexpected_run)

    assert manager.install_dependencies() is True


def test_install_dependencies_success(tmp_path, monkeypatch):
    requirements_file, state_file = configure_test_paths(
        tmp_path, monkeypatch
    )

    requirements_file.write_text(
        "requests==2.32.3\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        manager,
        "confirm_installation",
        lambda: True,
    )

    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs

        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(manager.subprocess, "run", fake_run)

    result = manager.install_dependencies()

    assert result is True
    assert captured["command"][1:3] == ["-m", "pip"]
    assert "install" in captured["command"]
    assert "-r" in captured["command"]
    assert state_file.is_file()


def test_installation_declined(tmp_path, monkeypatch):
    requirements_file, state_file = configure_test_paths(
        tmp_path, monkeypatch
    )

    requirements_file.write_text(
        "requests==2.32.3\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        manager,
        "confirm_installation",
        lambda: False,
    )

    result = manager.install_dependencies()

    assert result is False
    assert not state_file.exists()


def test_installation_failure(tmp_path, monkeypatch):
    requirements_file, state_file = configure_test_paths(
        tmp_path, monkeypatch
    )

    requirements_file.write_text(
        "requests==2.32.3\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        manager,
        "confirm_installation",
        lambda: True,
    )

    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            1, args[0]
        )

    monkeypatch.setattr(manager.subprocess, "run", fake_run)

    with pytest.raises(
        RuntimeError,
        match="Failed to install dependencies for tool",
    ):
        manager.install_dependencies()

    assert not state_file.exists()


def test_missing_requirements_file(tmp_path, monkeypatch):
    requirements_file, _ = configure_test_paths(
        tmp_path, monkeypatch
    )

    assert not requirements_file.exists()

    with pytest.raises(FileNotFoundError):
        manager.install_dependencies()

