import logging
import os
import tarfile
from urllib.parse import urlparse
import requests
from s3_util import S3Store, parse_s3_uri, validate_s3_uri
from base_util import get_asset_info, validate_http_uri
from config import model_base_dir, w_model, s3_endpoint_url


def extract_model(
    w_model: str, model_base_dir: str, destination: str, asset_id: str, extension: str
) -> str:
    logger = logging.getLogger(__name__)
    logger.info(f"Downloaded {w_model} into {model_base_dir}")
    if not os.path.exists(destination):  # Create dir for model to be extracted in
        os.makedirs(destination)
    logger.info(f"Extracting the model into {destination}")
    tar_path = model_base_dir + "/" + asset_id + "." + extension
    with tarfile.open(tar_path) as tar:
        tar.extractall(path=destination)
    # cleanup: delete the tar file
    os.remove(tar_path)
    return model_base_dir + "/" + asset_id


# makes sure the model is obtained from S3/HTTP/Huggingface, if w_model doesn't exist locally
def check_model_availability() -> str:
    logger = logging.getLogger(__name__)

    if validate_s3_uri(w_model):
        logger.info(f"{w_model} is an S3 URI. Attempting to download")
        bucket, object_name = parse_s3_uri(w_model)
        asset_id, extension = get_asset_info(object_name)
        destination = model_base_dir + "/" + asset_id
        if os.path.exists(destination):
            logger.info("Model already exists")
            return model_base_dir + "/" + asset_id
        s3 = S3Store(s3_endpoint_url)
        success = s3.download_file(bucket, object_name, model_base_dir)
        if not success:
            logger.error(f"Could not download {w_model} into {model_base_dir}")
            return ""
        return extract_model(w_model, model_base_dir, destination, asset_id, extension)

    elif validate_http_uri(w_model):
        logger.info(f"{w_model} is an HTTP URI. Attempting to download")
        asset_id, extension = get_asset_info(urlparse(w_model).path)
        destination = model_base_dir + "/" + asset_id
        if os.path.exists(destination):
            logger.info("Model already exists")
            return model_base_dir + "/" + asset_id
        with open(model_base_dir + "/" + asset_id + "." + extension, "wb") as file:
            response = requests.get(w_model)
            if response.status_code >= 400:
                logger.error(f"Could not download {w_model} into {model_base_dir}")
                return ""
            file.write(response.content)
            file.close()
        return extract_model(w_model, model_base_dir, destination, asset_id, extension)

    # The faster-whisper API can auto-detect if the version exists locally. No need to add extra checks
    logger.info(f"{w_model} is not an S3/HTTP URI. Using HuggingFace instead")
    return w_model
