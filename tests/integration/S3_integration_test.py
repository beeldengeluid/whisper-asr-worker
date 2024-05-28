from moto import mock_aws
import boto3
import pytest
import os
import shutil
import tarfile

from main_data_processor import run
from dane.config import cfg
from io_util import untar_input_file, S3_OUTPUT_TYPES


carrier_id = "carrier"
resource_id = "resource__" + carrier_id
fn_tar_in = f"{resource_id}.tar.gz"
key_in = f"{cfg.INPUT.S3_FOLDER_IN_BUCKET}/{fn_tar_in}"
tar_out = f"{carrier_id}/out__{carrier_id}.tar.gz"
key_out = f"{cfg.OUTPUT.S3_FOLDER_IN_BUCKET}/{tar_out}"
model_tar = "model.tar.gz"


@pytest.fixture
def aws_credentials():
    """Create custom AWS setup: mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"  # Other regions make stuff complex
    os.environ["MOTO_S3_CUSTOM_ENDPOINTS"] = cfg.INPUT.S3_ENDPOINT_URL


@pytest.fixture
def aws(aws_credentials):
    """Spin up local aws for testing"""
    with mock_aws():
        yield boto3.client("s3")


@pytest.fixture
def create_sample_input():
    """
    Add sample input for test to input bucket.
    """
    fn = (
        f"{cfg.FILE_SYSTEM.BASE_MOUNT}/"
        f"{cfg.FILE_SYSTEM.INPUT_DIR}/"
        f"{cfg.INPUT.TEST_INPUT_PATH}"
    )
    with tarfile.open(fn_tar_in, "w:gz") as tar:
        tar.add(fn, arcname="inputfile.wav")
    yield
    # after test: cleanup
    os.remove(fn_tar_in)


@pytest.fixture
def create_and_fill_buckets(aws, create_sample_input):
    """Make sure input and output buckets exist, and add sample input"""
    client = boto3.client("s3")
    for bucket in [
        cfg.INPUT.S3_BUCKET,
        cfg.OUTPUT.S3_BUCKET,
        cfg.INPUT.S3_BUCKET_MODEL,
    ]:
        client.create_bucket(Bucket=bucket)
    client.upload_file(
        Filename=fn_tar_in,
        Bucket=cfg.INPUT.S3_BUCKET,
        Key=key_in,
    )


@pytest.fixture
def setup_fs():
    """Create test output dir, abort if dir is not empty."""
    try:
        os.makedirs(carrier_id)
    except FileExistsError:
        print("Destination for output is not empty: abort.")
        assert False
    yield
    # after test: cleanup
    shutil.rmtree(carrier_id)


def test_main_data_processor(aws, aws_credentials, create_and_fill_buckets, setup_fs):
    """Test the main_data_processor.run function, running on URI in mocked S3.
    Relies on fixtures: aws, aws_credentials, create_and_fill_buckets, setup_fs"""
    if cfg.OUTPUT.TRANSFER_ON_COMPLETION:
        # run the main data processor
        run(input_file_path=f"s3://{cfg.INPUT.S3_BUCKET}/{key_in}")

        # Check if the output is present in S3
        client = boto3.client("s3")
        found = False
        for item in client.list_objects(Bucket=cfg.OUTPUT.S3_BUCKET)["Contents"]:
            found = item["Key"] == key_out
            if found:
                break
        assert found

        client.download_file(Bucket=cfg.OUTPUT.S3_BUCKET, Key=key_out, Filename=tar_out)
        untar_input_file(tar_out)
        for type in S3_OUTPUT_TYPES:
            assert type.value in os.listdir(carrier_id)

    else:
        print("Not configured to transfer output!")
        assert False
