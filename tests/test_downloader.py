import hashlib
import pytest

from primetoolv3.core.downloader import calculate_sha256, parse_checksums
from primetoolv3.core import downloader
from primetoolv3.core.version_manager import ReleaseInfo

def test_calculate_sha256(tmp_path):
    file_path = tmp_path / "tool.py"
    content = b"print('Hello from MyConverter')"

    file_path.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()

    assert calculate_sha256(file_path) == expected


def test_parse_valid_checksums(tmp_path):
    checksum_file = tmp_path / "checksums.txt"

    checksum_file.write_text(
        "a" * 64 + "  tool.py\n" +
        "b" * 64 + "  requirements.txt\n",
        encoding="utf-8",
    )

    checksums = parse_checksums(checksum_file)

    assert checksums == {
        "tool.py": "a" * 64,
        "requirements.txt": "b" * 64,
    }


def test_parse_invalid_checksum(tmp_path):
    checksum_file = tmp_path / "checksums.txt"

    checksum_file.write_text(
        "invalid-hash  tool.py\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Invalid SHA-256 hash"):
        parse_checksums(checksum_file)


def test_parse_unexpected_filename(tmp_path):
    checksum_file = tmp_path / "checksums.txt"

    checksum_file.write_text(
        "a" * 64 + "  engine/tool.py\n" +
        "b" * 64 + "  requirements.txt\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Invalid checksum filename"):
        parse_checksums(checksum_file)

def test_failed_download_preserves_existing_cache(tmp_path, monkeypatch):
    app_dir = tmp_path / "app"
    script_dir = app_dir / "scripts"

    app_dir.mkdir()
    script_dir.mkdir()

    # Simulate an existing working installation.
    old_tool = script_dir / "tool.py"
    old_tool.write_text("print('old working tool')", encoding="utf-8")

    old_requirements = script_dir / "requirements.txt"
    old_requirements.write_text("# old requirements", encoding="utf-8")

    old_checksums = script_dir / "checksums.txt"
    old_checksums.write_text("old checksum manifest", encoding="utf-8")

    new_tool = b"print('new tool')"
    new_requirements = b"# new requirements"

    tool_hash = hashlib.sha256(new_tool).hexdigest()
    requirements_hash = hashlib.sha256(new_requirements).hexdigest()

    manifest = (
        f"{tool_hash}  tool.py\n"
        f"{requirements_hash}  requirements.txt\n"
    ).encode()

    monkeypatch.setattr(downloader, "ensure_app_dirs", lambda: None)
    monkeypatch.setattr(downloader, "get_app_dir", lambda: app_dir)
    monkeypatch.setattr(downloader, "get_script_dir", lambda: script_dir)

    def fake_download_file(url, destination):
        if destination.name == "checksums.txt":
            destination.write_bytes(manifest)
        elif destination.name == "tool.py":
            # Deliberately corrupt the downloaded file.
            destination.write_bytes(b"corrupted tool")
        elif destination.name == "requirements.txt":
            destination.write_bytes(new_requirements)

    monkeypatch.setattr(downloader, "download_file", fake_download_file)

    release = ReleaseInfo(
        tag_name="v1.0.2",
        version="1.0.2",
        name="Test Release",
        published_at="2026-11-15T00:00:00Z",
        html_url="https://github.com/example/repo/releases/tag/v1.0.2",
        assets={
            "tool.py": "https://example.com/tool.py",
            "requirements.txt": "https://example.com/requirements.txt",
            "checksums.txt": "https://example.com/checksums.txt",
        }
    )

    with pytest.raises(RuntimeError, match="Checksum verification failed"):
        downloader.download_release_assets(release)

    # Previous installation must remain untouched.
    assert old_tool.read_text(encoding="utf-8") == "print('old working tool')"
    assert old_requirements.read_text(encoding="utf-8") == "# old requirements"
    assert old_checksums.read_text(encoding="utf-8") == "old checksum manifest"

def test_download_file_removes_partial_file(tmp_path, monkeypatch):
    destination = tmp_path / "tool.py"

    class FakeResponse:
        def __init__(self):
            self.calls = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size):
            self.calls += 1

            if self.calls == 1:
                return b"partial content"

            raise OSError("Connection interrupted")

    monkeypatch.setattr(
        downloader,
        "urlopen",
        lambda *args, **kwargs: FakeResponse(),
    )

    with pytest.raises(OSError, match="Connection interrupted"):
        downloader.download_file(
            "https://github.com/example/repo/releases/download/v1.0.0/tool.py",
            destination,
        )

    assert not destination.exists()

