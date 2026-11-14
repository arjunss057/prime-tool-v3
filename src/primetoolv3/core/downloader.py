import hashlib
import os
import re
import shutil
import tempfile

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from primetoolv3.config import REQUEST_TIMEOUT, CHUNK_SIZE, REQUIRED_ASSETS
from primetoolv3.utils.paths import get_app_dir, get_script_dir, ensure_app_dirs
from primetoolv3.core.version_manager import ReleaseInfo

def calculate_sha256(file_path: Path) -> str:
    '''
    Calculate SHA-256 checksum of a file
    '''
    sha256 = hashlib.sha256()
    with file_path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url: str, destination: Path) -> None:
    '''
    Download a file over HTTPS
    '''
    if urlparse(url).scheme != "https":
        raise RuntimeError("Only HTTPS downloads are permitted")
    request = Request(url, headers={"User-Agent": "PrimeToolv3-CLI"})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            with destination.open("wb") as file:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    file.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

def parse_checksums(checksum_file: Path) -> dict[str, str]:
    '''
    Parse SHA-256 checksum manifest
    Expected format:
    
    <hash>  tool.py
    <hash>  requirements.txt
    '''

    checksums = {}
    with checksum_file.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                raise RuntimeError("Invalid checksum manifest format")
            checksum, filename = parts
            filename = filename.lstrip("*")
            if not re.fullmatch(r"[a-fA-F0-9]{64}", checksum):
                raise RuntimeError(f"Invalid SHA-256 hash for {filename}")
            if filename not in REQUIRED_ASSETS - {"checksums.txt"}:
                raise RuntimeError(f"Unexpected checksum entry: {filename}")
            if filename in checksums:
                raise RuntimeError(f"Duplicate checksum entry: {filename}")
            checksums[filename] = checksum.lower()
    expected = REQUIRED_ASSETS - {"checksums.txt"}
    if set(checksums) != expected:
        raise RuntimeError("Checksum manifest is missing required files")
    return checksums

def verify_checksums(directory: Path) -> None:
    '''
    Verify all downloaded files against checksums.txt
    '''
    checksum_file = directory/"checksums.txt"
    if not checksum_file.is_file():
        raise RuntimeError("Checksum manifest is missing")
    checksums = parse_checksums(checksum_file)
    for filename, expected_hash in checksums.items():
        file_path = directory/filename
        if not file_path.is_file():
            raise RuntimeError(f"Missing release asset: {filename}")
        actual_hash = calculate_sha256(file_path)
        if actual_hash != expected_hash:
            raise RuntimeError(f"Checksum verification failed: {filename}")

def verify_cached_assets(directory: Path) -> bool:
    '''
    Validate an existing local tool cache
    '''
    try:
        if not directory.is_dir():
            return False
        if not all((directory/filename).is_file() for filename in REQUIRED_ASSETS):
            return False
        verify_checksums(directory)
        return True
    except (OSError, RuntimeError, ValueError):
        return False

def download_release_assets(release: ReleaseInfo) -> Path:
    '''
    Download, validate and install release assets
    Existing cached files are preserved if downloading or checksum verification fails
    '''
    ensure_app_dirs()
    missing_assets = REQUIRED_ASSETS - set(release.assets)
    if missing_assets:
        raise RuntimeError("Release is missing assets: " + ", ".join(sorted(missing_assets)))
    app_dir = get_app_dir()
    script_dir = get_script_dir()
    with tempfile.TemporaryDirectory(prefix=".download-", dir=app_dir) as temporary_directory:
        staging_dir = Path(temporary_directory)
        download_file(release.assets["checksums.txt"], staging_dir/"checksums.txt")
        for filename in ("tool.py", "requirements.txt"):
            download_file(release.assets[filename], staging_dir/filename)
        verify_checksums(staging_dir)
        backup_dir = app_dir/".script-backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        if script_dir.exists():
            os.replace(script_dir, backup_dir)
        try:
            os.replace(staging_dir, script_dir)
        except Exception:
            if backup_dir.exists():
                os.replace(backup_dir, script_dir)
            raise
        else:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
    return script_dir