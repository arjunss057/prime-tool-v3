import os
from pathlib import Path
from primetoolv3.config import APP_NAME

def get_app_dir() -> Path:
    '''
    Return the application data directory
    '''
    if os.name == "nt":
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home()/"AppData"/"Local"))
        return base_dir/APP_NAME
    return Path.home()/".primetoolv3"

def get_script_dir() -> Path:
    return get_app_dir()/"script"

def get_metadata_dir() -> Path:
    return get_app_dir()/"metadata"

def get_logs_dir() -> Path:
    return get_app_dir()/"logs"

def get_version_file() -> Path:
    return get_metadata_dir()/"version.json"

def ensure_app_dirs() -> None:
    '''
    Create all required application directories
    '''
    directories = [
        get_app_dir(),
        get_script_dir(),
        get_metadata_dir(),
        get_logs_dir()
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_venv_dir() -> Path:
    return get_app_dir()/"venv"

def get_dependency_state_file() -> Path:
    return get_metadata_dir()/"dependencies.json"