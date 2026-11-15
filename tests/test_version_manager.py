import pytest
from primetoolv3.core.version_manager import parse_version, compare_versions

@pytest.mark.parametrize(
        "version, expected",
        [
            ("1.0.0", (1, 0, 0)),
            ("v1.0.0", (1, 0, 0)),
            ("v1.2.3", (1, 2, 3)),
            ("2.10.5", (2, 10, 5)),
            ("v10.20.30", (10, 20, 30))
        ]
)

def test_parse_version(version, expected):
    assert parse_version(version) == expected

@pytest.mark.parametrize(
        "version",
        [
            "",
            "latest",
            "v1.2",
            "1.2.3.4",
            "v1.x.3"
        ]
)

def test_parse_invalid_version(version):
    with pytest.raises(ValueError):
        parse_version(version)

@pytest.mark.parametrize(
    "remote, local, expected",
    [
        ("1.0.1", "1.0.0", 1),
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "1.0.1", -1),
        ("2.0.0", "1.9.9", 1),
        ("1.10.0", "1.9.0", 1)
    ]
)
def test_compare_versions(remote, local, expected):
    assert compare_versions(remote, local) == expected