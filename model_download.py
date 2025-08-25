import logging
import os
import tarfile
from urllib.parse import urlparse
import requests
from s3_util import S3Store, parse_s3_uri, validate_s3_uri
from base_util import get_asset_info, validate_http_uri
from config import MODEL_S3_ENDPOINT_URL


logger = logging.getLogger(__name__)


# e.g. {base_dir}/modelx.tar.gz will be extracted in {base_dir}/modelx
def extract_model(destination: str, extension: str) -> str:
    tar_path = f"{destination}.{extension}"
    logger.info(f"Extracting  {tar_path} into {destination}")
    if not os.path.exists(destination):  # Create dir for model to be extracted in
        os.makedirs(destination)
    logger.info(f"Extracting the model into {destination}")
    with tarfile.open(tar_path) as tar:
        tar.extractall(path=destination)
    # cleanup: delete the tar file
    os.remove(tar_path)
    if os.path.exists(os.path.join(destination, "model.bin")):
        logger.info(f"model.bin found in {destination}. Model extracted successfully!")
        return destination
    else:
        raise Exception(f"{destination} does not contain a model.bin file. Exiting...")


# makes sure the model is obtained from S3/HTTP/Huggingface,
# if w_model doesn't exist locally
def get_model_location(base_dir: str, whisper_model: str) -> str:
    logger.info(f"Checking w_model: {whisper_model} and download if necessary")
    if validate_s3_uri(whisper_model):
        return check_s3_location(base_dir, whisper_model)

    elif validate_http_uri(whisper_model):
        return check_http_location(base_dir, whisper_model)

    # The faster-whisper API can auto-detect if the version exists locally.
    # No need to add extra checks
    logger.info(f"{whisper_model} is not an S3/HTTP URI. Using HuggingFace instead")
    return whisper_model


def check_s3_location(base_dir: str, whisper_model: str) -> str:
    logger.info(f"{whisper_model} is an S3 URI. Attempting to download")
    bucket, object_name = parse_s3_uri(whisper_model)
    asset_id, extension = get_asset_info(object_name)
    destination = os.path.join(base_dir, asset_id)
    if os.path.exists(destination):
        logger.info("Model already exists")
        return destination
    s3 = S3Store(MODEL_S3_ENDPOINT_URL)
    success = s3.download_file(bucket, object_name, base_dir)
    if not success:
        raise Exception(f"Could not download {whisper_model} into {base_dir}")
    return extract_model(destination, extension)


def check_http_location(base_dir: str, whisper_model: str) -> str:
    logger.info(f"{whisper_model} is an HTTP URI. Attempting to download")
    asset_id, extension = get_asset_info(urlparse(whisper_model).path)
    destination = os.path.join(base_dir, asset_id)
    if os.path.exists(destination):
        logger.info("Model already exists")
        return destination
    with open(f"{destination}.{extension}", "wb") as file:
        response = requests.get(whisper_model)
        if response.status_code >= 400:
            raise Exception(f"Could not download {whisper_model} into {base_dir}")
        file.write(response.content)
        file.close()
    return extract_model(destination, extension)
