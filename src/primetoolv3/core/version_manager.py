import json
import re

from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Optional

from primetoolv3.config import GITHUB_LATEST_RELEASE_URL, REQUEST_TIMEOUT
from primetoolv3.utils.paths import get_version_file, get_metadata_dir

@dataclass(frozen=True)
class ReleaseInfo:
    tag_name: str
    version: str
    name: str
    published_at: str
    html_url: str
    assets: dict[str, str]

def parse_version(tag: str) -> tuple:
    '''
    Convert a release tag into a numeric version tuple.
    Supports tags such as v1.0.0 and 1.0.0
    '''

    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", tag)
    if not match:
        raise ValueError(f"Invalid release version: {tag}")
    return tuple(map(int, match.groups()))

def compare_versions(remote_version: str, local_version: str) -> int:
    '''
    Compare two semantic versions
    
    Returns:
        1   : Remote version is newer
        0   : Versions are equal
        -1  : Remote version is older
    '''

    remote = parse_version(remote_version)
    local = parse_version(local_version)
    if remote > local:
        return 1
    if remote < local:
        return -1
    return 0

def get_latest_release() -> ReleaseInfo:
    '''
    Retrieve the latest published GitHub release
    '''

    request = Request(
        GITHUB_LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PrimeToolV3-CLI"
        }
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"GitHub API error: {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"Unable to connect to GitHub: {error.reason}") from error
    except (TimeoutError, OSError) as error:
        raise RuntimeError(f"GitHub Connection failed: {error}") from error
    
    tag = data.get("tag_name")
    if not isinstance(tag, str):
        raise RuntimeError("GitHub release does not contain a valid tag. ")

    try:
        version_tuple = parse_version(tag)
    except ValueError as error:
        raise RuntimeError(str(error)) from error

    assets = {}
    for asset in data.get("assets", []):
        name = asset.get("name")
        download_url = asset.get("browser_download_url")
        if name and download_url:
            assets[name] = download_url
    return ReleaseInfo(
        tag_name=tag,
        version=".".join(map(str, version_tuple)),
        name= data.get("name") or tag,
        published_at=data.get("published_at") or "",
        html_url=data.get("html_url") or "",
        assets=assets
    )

def load_cached_release() -> Optional[dict]:
    '''
    Read locally cached release metadata
    '''
    version_file = get_version_file()
    if not version_file:
        return None
    try:
        with version_file.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

def save_cached_release(release: ReleaseInfo) -> None:
    '''
    Atomically save release metadata.
    '''
    metadata_dir = get_metadata_dir()
    version_file = get_version_file()
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "tag_name": release.tag_name,
        "version": release.version,
        "name": release.name,
        "published_at": release.published_at,
        "html_url": release.html_url
    }
    temporary_file = version_file.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)
            file.flush()
        temporary_file.replace(version_file)
    finally:
        temporary_file.unlink(missing_ok=True)
