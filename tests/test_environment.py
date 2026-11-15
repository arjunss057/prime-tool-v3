
from types import SimpleNamespace

from primetoolv3.core import environment


def test_get_venv_python():
    python_path = environment.get_venv_python()

    if environment.os.name == "nt":
        assert python_path.name == "python.exe"
        assert python_path.parent.name == "Scripts"
    else:
        assert python_path.name == "python"
        assert python_path.parent.name == "bin"


def test_environment_exists(tmp_path, monkeypatch):
    venv_dir = tmp_path / "venv"

    monkeypatch.setattr(
        environment,
        "get_venv_dir",
        lambda: venv_dir,
    )

    assert environment.environment_exists() is False

    python_path = environment.get_venv_python()
    python_path.parent.mkdir(parents=True)
    python_path.touch()

    assert environment.environment_exists() is True


def test_create_environment(tmp_path, monkeypatch):
    venv_dir = tmp_path / "venv"

    monkeypatch.setattr(
        environment,
        "get_venv_dir",
        lambda: venv_dir,
    )

    def fake_run(command, **kwargs):
        assert command[1:3] == ["-m", "venv"]

        target = venv_dir

        if environment.os.name == "nt":
            python_path = target / "Scripts" / "python.exe"
        else:
            python_path = target / "bin" / "python"

        python_path.parent.mkdir(parents=True, exist_ok=True)
        python_path.touch()

        return SimpleNamespace(
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(environment.subprocess, "run", fake_run)

    result = environment.create_environment()

    assert result.is_file()
    assert environment.environment_exists()


def test_create_environment_reuses_existing(tmp_path, monkeypatch):
    venv_dir = tmp_path / "venv"

    monkeypatch.setattr(
        environment,
        "get_venv_dir",
        lambda: venv_dir,
    )

    python_path = environment.get_venv_python()
    python_path.parent.mkdir(parents=True)
    python_path.touch()

    def unexpected_run(*args, **kwargs):
        raise AssertionError("Existing environment should be reused")

    monkeypatch.setattr(environment.subprocess, "run", unexpected_run)

    assert environment.create_environment() == python_path


def test_create_environment_detects_incomplete_venv(
    tmp_path, monkeypatch
):
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()

    monkeypatch.setattr(
        environment,
        "get_venv_dir",
        lambda: venv_dir,
    )

    try:
        environment.create_environment()
        assert False, "Expected RuntimeError"
    except RuntimeError as error:
        assert "Incomplete virtual environment" in str(error)


def test_remove_environment(tmp_path, monkeypatch):
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    (venv_dir / "dummy.txt").touch()

    monkeypatch.setattr(
        environment,
        "get_venv_dir",
        lambda: venv_dir,
    )

    environment.remove_environment()

    assert not venv_dir.exists()
