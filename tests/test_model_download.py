import tarfile
import pytest
import shutil
import os

# Mocking environment used in model_download
os.environ["DATA_BASE_DIR"] = "data"
os.environ["MODEL_BASE_DIR"] = "tests/input/extract_model_test"
os.environ["S3_ENDPOINT_URL"] = "http://url.com"

from model_download import extract_model, get_model_location  # noqa


@pytest.mark.parametrize(
    "destination, extension, expected_output",
    [("valid_model", "tar.gz", "valid_model")],
)
def test_extract_valid_model(destination, extension, expected_output, tmp_path):
    tar_path = os.path.join("tests/input/extract_model_test", destination)
    shutil.copy(f"{tar_path}.{extension}", str(tmp_path))
    expected_output = os.path.join(tmp_path, expected_output)
    assert (
        extract_model(os.path.join(tmp_path, destination), extension) == expected_output
    )


@pytest.mark.parametrize(
    "destination, extension, expected_output",
    [("valid_model", "mp3", "")],
)
def test_extract_wrong_extension(destination, extension, expected_output, tmp_path):
    tar_path = os.path.join("tests/input/extract_model_test", destination)
    shutil.copy(f"{tar_path}.{extension}", str(tmp_path))
    with pytest.raises(tarfile.ReadError):
        assert (
            extract_model(os.path.join(tmp_path, destination), extension)
            == expected_output
        )


@pytest.mark.parametrize(
    "destination, extension, expected_output",
    [
        ("invalid_model", "tar.gz", ""),
    ],
)
def test_extract_invalid_model(destination, extension, expected_output, tmp_path):
    tar_path = os.path.join("tests/input/extract_model_test", destination)
    shutil.copy(f"{tar_path}.{extension}", str(tmp_path))
    with pytest.raises(Exception):
        assert (
            extract_model(os.path.join(tmp_path, destination), extension)
            == expected_output
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
