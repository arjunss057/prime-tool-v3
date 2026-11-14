import hashlib
import json
import subprocess
from pathlib import Path

from primetoolv3.core.environment import environment_exists, get_venv_python
from primetoolv3.utils.paths import get_dependency_state_file, get_metadata_dir, get_script_dir

def get_requirements_file() -> Path:
    return get_script_dir()/"requirements.txt"

def calculate_requirements_hash() -> str:
    """Calculate SHA-256 hash of the requirements file"""
    requirements_file = get_requirements_file()
    if not requirements_file.is_file():
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
    sha256 = hashlib.sha256()
    with requirements_file.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def has_installable_requirements() -> bool:
    """Check whether requirements.txt contains any active entries"""
    requirements_file = get_requirements_file()
    with requirements_file.open("r", encoding="utf-8") as file:
        return any(line.strip() and not line.strip().startswith("#") for line in file)

def dependencies_are_current(requirements_hash: str) -> bool:
    """Check whether the current requirements were already installed"""
    state_file = get_dependency_state_file()
    if not state_file.is_file():
        return False
    try:
        with state_file.open("r", encoding="utf-8") as file:
            state = json.load(file)
        return state.get("requirements_hash") == requirements_hash
    except (OSError, json.JSONDecodeError):
        return False

def save_dependency_state(requirements_hash: str) -> None:
    """Save the hash of successfully processed requirements"""
    state_file = get_dependency_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = state_file.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(
            {"requirements_hash": requirements_hash},
            file,
            indent=4
        )
    temporary_file.replace(state_file)

def confirm_installation() -> bool:
    """Ask the user for permission before installing dependencies."""

    print("\nThe tool requires additional python packages. ")
    try:
        choice = input("Install dependencies? [y/n]: ")
    except EOFError:
        return False
    return choice.strip().lower() in {"y", "yes"}

def install_dependencies() -> bool:
    """
    Install the tool dependences into its isolated environment
    Returns True if dependencies are ready, False if the user declines. 
    """

    if not environment_exists():
        raise RuntimeError("Virtual environment for tool does not exist. ")
    requirements_file = get_requirements_file()
    if not requirements_file.is_file():
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
    requirements_hash = calculate_requirements_hash()
    if dependencies_are_current(requirements_hash):
        print("Dependencies for tool are already up to date")
        return True
    if not has_installable_requirements():
        print("No third-party dependencies are required")
        save_dependency_state(requirements_hash)
        return True
    if not confirm_installation():
        print("Dependency installation cancelled")
        return False
    venv_python = get_venv_python()
    print("Installing dependencies for tool...")
    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requirements_file)], check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Failed to install dependencies for tool") from exc
    save_dependency_state(requirements_hash)
    print("Dependencies for tool installed successfully")
    return True

