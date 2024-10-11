from dataclasses import dataclass
import logging
import os
import requests
import time
from urllib.parse import urlparse
from s3_util import S3Store, parse_s3_uri, validate_s3_uri
from config import data_base_dir, s3_endpoint_url
from base_util import get_asset_info, extension_to_mime_type, validate_http_uri

logger = logging.getLogger(__name__)

input_file_dir = os.path.join(data_base_dir, "input/")


@dataclass
class DownloadResult:
    file_path: str  # target_file_path,  # TODO harmonize with dane-download-worker
    mime_type: str
    provenance: dict
    download_time: float = -1  # time (ms) taken to receive data after request
    content_length: int = -1  # download_data.get("content_length", -1),
    error: str = ""


def download_uri(uri: str) -> DownloadResult:
    logger.info(f"Trying to download {uri}")
    if validate_s3_uri(uri):
        logger.info("URI seems to be an S3 URI")
        return s3_download(uri)
    if validate_http_uri(uri):
        logger.info("URI seems to be an HTTP URI")
        return http_download(uri)
    return DownloadResult(
        uri, "", dict(), -1, "Input failure: URI is neither S3, nor HTTP"
    )


def http_download(url: str) -> DownloadResult:
    logger.info(f"Checking if {url} was already downloaded")
    steps = []  # to report if input is already downloaded

    fn = os.path.basename(urlparse(url).path)
    input_file = os.path.join(input_file_dir, fn)
    _, extension = get_asset_info(input_file)
    mime_type = extension_to_mime_type(extension)

    # download if the file is not present (preventing unnecessary downloads)
    start_time = time.time()
    download_time = -1

    if not os.path.exists(input_file):
        logger.info(f"File {input_file} not downloaded yet")
        # Create /data/input/ folder if not exists
        if not os.path.exists(input_file_dir):
            logger.info(f"{input_file_dir} does not exist, creating it now")
            os.makedirs(input_file_dir)
        with open(input_file, "wb") as file:
            response = requests.get(url)
            if response.status_code >= 400:
                logger.error(f"Could not download url: {response.status_code}")
                download_time = (time.time() - start_time) * 1000
                return DownloadResult(
                    input_file, mime_type, dict(), download_time, f"Input failure: Could not download url. Response code: {response.status_code}"
                )
            file.write(response.content)
            file.close()
        download_time = (time.time() - start_time) * 1000  # time in ms
    else:
        steps.append("Download skipped: input already exists")
    provenance = {
        "activity_name": "Input download",
        "activity_description": "Downloads the input file from INPUT_URI",
        "processing_time_ms": download_time,
        "start_time_unix": start_time,
        "parameters": [],
        "software_version": "",
        "input_data": url,
        "output_data": input_file,
        "steps": steps,
    }
    return DownloadResult(
        input_file, mime_type, provenance, download_time  # TODO add content_length
    )


def s3_download(s3_uri: str) -> DownloadResult:
    logger.info(f"Checking if {s3_uri} was already downloaded")
    steps = []  # to report if input is already downloaded

    # parse S3 URI
    bucket, object_name = parse_s3_uri(s3_uri)
    logger.info(f"OBJECT NAME: {object_name}")
    input_file = os.path.join(
        input_file_dir,
        os.path.basename(object_name),  # i.e. visxp_prep__<source_id>.tar.gz
    )

    _, extension = get_asset_info(input_file)
    mime_type = extension_to_mime_type(extension)

    start_time = time.time()
    download_time = -1

    if not os.path.exists(input_file):
        s3 = S3Store(s3_endpoint_url)
        # Create /data/input/ folder if not exists
        if not os.path.exists(input_file_dir):
            logger.info(f"{input_file_dir} does not exist, creating it now")
            os.makedirs(input_file_dir)
        success = s3.download_file(bucket, object_name, input_file_dir)

        if not success:
            logger.error("Failed to download input data from S3")
            download_time = (time.time() - start_time) * 1000
            return DownloadResult(
                input_file, mime_type, dict(), download_time, "Input failure: Could not download S3 URI"
            )

        download_time = int((time.time() - start_time) * 1000)  # time in ms
    else:
        steps.append("Download skipped: input already exists")

    provenance = {
        "activity_name": "Input download",
        "activity_description": "Downloads the input file from INPUT_URI",
        "processing_time_ms": download_time,
        "start_time_unix": start_time,
        "parameters": [],
        "software_version": "",
        "input_data": s3_uri,
        "output_data": input_file,
        "steps": steps,
    }

    return DownloadResult(
        input_file, mime_type, provenance, download_time  # TODO add content_length
    )
