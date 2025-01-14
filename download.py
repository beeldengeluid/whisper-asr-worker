from dataclasses import dataclass
import logging
import os
import requests
import time
from s3_util import S3Store, parse_s3_uri, validate_s3_uri
from config import S3_ENDPOINT_URL
from base_util import (
    extension_to_mime_type,
    validate_http_uri,
    Provenance,
    remove_all_input_output,
)

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    file_path: str  # target_file_path,
    mime_type: str
    provenance: Provenance
    content_length: int = -1  # download_data.get("content_length", -1),


def download_uri(
    uri: str, input_dir: str, filename: str, extension: str
) -> DownloadResult:
    logger.info(f"Trying to download {uri}")
    if validate_s3_uri(uri):
        logger.info("URI seems to be an S3 URI")
        return s3_download(uri, input_dir, filename, extension)
    if validate_http_uri(uri):
        logger.info("URI seems to be an HTTP URI")
        return http_download(uri, input_dir, filename, extension)
    raise Exception("Input failure: URI is neither S3, nor HTTP")


def http_download(
    url: str, input_dir: str, filename: str, extension: str
) -> DownloadResult:
    logger.info(f"Checking if {url} was already downloaded")
    start_time = time.time()

    provenance = Provenance(
        activity_name="Download Input",
        activity_description="Downloads the input file to be transcribed",
        start_time_unix=start_time,
        input_data=url,
    )

    input_file = os.path.join(input_dir, filename)
    mime_type = extension_to_mime_type(extension)

    if os.path.exists(input_file):
        logger.info(f"File {input_file} already exists, overwriting...")
        remove_all_input_output(input_dir)

    # Create /data/<asset_id>/ folder if not exists
    if not os.path.exists(input_dir):
        logger.info(f"{input_dir} does not exist, creating it now")
        os.makedirs(input_dir)
    with open(input_file, "wb") as file:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(
                f"Could not download {url}. Response code: {response.status_code}"
            )
        file.write(response.content)
        file.close()
    provenance.processing_time_ms = (time.time() - start_time) * 1000

    return DownloadResult(input_file, mime_type, provenance)  # TODO add content_length


def s3_download(
    url: str, input_dir: str, filename: str, extension: str
) -> DownloadResult:
    logger.info(f"Checking if {url} was already downloaded")
    start_time = time.time()

    provenance = Provenance(
        activity_name="Download Input",
        activity_description="Downloads the input file to be transcribed",
        start_time_unix=start_time,
        input_data=url,
    )

    # parse S3 URI
    bucket, object_name = parse_s3_uri(url)
    logger.info(f"OBJECT NAME: {object_name}")
    input_file = os.path.join(
        input_dir,
        os.path.basename(filename),  # i.e. visxp_prep__<source_id>.tar.gz
    )
    mime_type = extension_to_mime_type(extension)

    if os.path.exists(input_file):
        logger.info(f"File {input_file} already exists, attempting to delete")
        remove_all_input_output(input_dir)

    s3 = S3Store(S3_ENDPOINT_URL)
    # Create /data/<asset_id>/ folder if not exists
    if not os.path.exists(input_dir):
        logger.info(f"{input_dir} does not exist, creating it now")
        os.makedirs(input_dir)
    success = s3.download_file(bucket, object_name, input_dir)

    if not success:
        raise Exception(f"Could not download {url} from S3")

    provenance.processing_time_ms = (time.time() - start_time) * 1000  # time in ms

    return DownloadResult(input_file, mime_type, provenance)  # TODO add content_length
