import logging
import os
import tarfile
from s3_util import S3Store, parse_s3_uri, validate_s3_uri
from config import model_base_dir, w_model, s3_endpoint_url


# makes sure the model is available locally, if not download it from S3, if that fails download from Huggingface
# FIXME should also check if the correct w_model type is available locally!
def check_model_availability() -> bool:
    logger = logging.getLogger(__name__)
    if os.path.exists(model_base_dir + "/model.bin"):
        logger.info("Model found locally")
        return True
    else:
        logger.info("Model not found locally, attempting to download from S3")
        if not validate_s3_uri(w_model):
            logger.info("No S3 URI detected")
            logger.info(f"Downloading version {w_model} from Huggingface instead")
            return False
        s3 = S3Store(s3_endpoint_url)
        bucket, object_name = parse_s3_uri(w_model)
        success = s3.download_file(bucket, object_name, model_base_dir)
        if not success:
            logger.error(f"Could not download {w_model} into {model_base_dir}")
            return False
        logger.info(f"Downloaded {w_model} into {model_base_dir}")
        logger.info("Extracting the model")
        tar_path = model_base_dir + "/" + object_name
        with tarfile.open(tar_path) as tar:
            tar.extractall(path=model_base_dir)
        # cleanup: delete the tar file
        os.remove(tar_path)
        return True
