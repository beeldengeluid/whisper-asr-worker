import pytest
from s3_util import validate_s3_uri


@pytest.mark.parametrize(
    "s3_uri, expected_output",
    [
        ("s3://bucket/object.mp3", True),
        ("s3://bucket/path/object.mp3", True),
        ("s3://bucket/path/sub/object.mp3", True),
        ("s3://bucket/object", True),
        ("s3://object.mp4", False),  # bucket name missing
        ("http://bucket/object.mp4", False),  # wrong protocol
    ],
)
def test_validate_s3_uri(s3_uri, expected_output):
    assert validate_s3_uri(s3_uri) == expected_output
