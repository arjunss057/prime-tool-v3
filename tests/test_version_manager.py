import pytest
from primetoolv3.core.version_manager import parse_version, compare_versions

def test_parse_version():
    assert parse_version("v1.2.3") == (1, 2, 3)

def test_newer_version():
    assert compare_versions("1.2.0", "1.1.0") == 1

def test_same_version():
    assert compare_versions("1.0.0", "1.0.0") == 0

def test_older_version():
    assert compare_versions("1.0.0", "1.1.0") == -1

def test_invalid_version():
    with pytest.raises(ValueError):
        parse_version("latest")