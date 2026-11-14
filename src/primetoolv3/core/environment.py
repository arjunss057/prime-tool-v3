import os
import shutil
import subprocess
import sys
from pathlib import Path

from primetoolv3.utils.paths import get_venv_dir

def get_venv_python() -> Path:
    """Return the python executable inside the managed environment"""
    venv_dir = get_venv_dir()
    if os.name == "nt":
        return venv_dir/"Scripts"/"python.exe"
    return venv_dir/"bin"/"python"

def environment_exists() -> bool:
    """Check whether the managed environment has a python executable"""
    return get_venv_python().is_file()

def create_environment() -> Path:
    """Create isolated virtual environment for tool"""
    venv_dir = get_venv_dir()
    venv_python = get_venv_python()
    if environment_exists():
        return venv_python
    if venv_dir.exists():
        raise RuntimeError(f"Incomplete virtual environment found at {venv_dir}\nRun 'prime-tool-v3 clean' and try again")
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    print("Creating virtual environment for tool...")
    result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], capture_output=True, text=True)
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Failed to create virtual environment for tool: {details}\nOn Ubuntu/Debian, you may need to install the matching python3-venv package")
    if not environment_exists():
        raise RuntimeError("Virtual environment creation finished but its python executable was not found")
    print("Virtual environment for tool created successfully")
    return venv_python

def remove_environment() -> None:
    """Remove the managed virtual environment for tool"""
    venv_dir = get_venv_dir()
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
        print("Virtual environment for tool removed")
    else:
        print("No virtual environment for tool found")