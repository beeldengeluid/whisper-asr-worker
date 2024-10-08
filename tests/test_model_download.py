import pytest
import shutil
import os
from dotenv import load_dotenv

# Mocking environment used in model_download (by loading tests/.env)
load_dotenv()

from model_download import extract_model, get_model_location  # noqa


@pytest.mark.parametrize(
    "destination, extension, expected_output",
    [
        ("valid_model", "tar.gz", "valid_model"),
        ("valid_model", "mp3", ""),
        ("invalid_model", "tar.gz", ""),
    ],
)
def test_extract_model(destination, extension, expected_output, tmp_path):
    tar_path = os.path.join("tests/input/extract_model_test", destination)
    shutil.copy(f"{tar_path}.{extension}", str(tmp_path))
    if expected_output != "":
        expected_output = os.path.join(tmp_path, expected_output)
    assert (
        extract_model(os.path.join(tmp_path, destination), extension) == expected_output
    )


@pytest.mark.parametrize(
    "whisper_model, expected_output",
    [
        ("s3://test-model/assets/modeltest.tar.gz", "s3"),
        ("http://model-hosting.beng.nl/whisper-test.mp3", "http"),
        ("large-v2", "large-v2"),
    ],
)
def test_get_model_location(whisper_model, expected_output, mocker):
    mocker.patch("model_download.check_s3_location", return_value="s3")
    mocker.patch("model_download.check_http_location", return_value="http")
    assert get_model_location("model", whisper_model) == expected_output


# TODO: test check_s3_location (have to mock: S3Store, s3.dl_file, extract_model)

# TODO: test check_http_location (have to mock: whole "with" block?, extract_model)
