from dataclasses import dataclass
import logging
import os
import requests
import time
from typing import Optional
from urllib.parse import urlparse
from s3_util import S3Store, parse_s3_uri, validate_s3_uri
from config import output_base_dir, s3_endpoint_url

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    file_path: str  # target_file_path,  # TODO harmonize with dane-download-worker
    download_time: float = -1  # time (secs) taken to receive data after request
    mime_type: str = "unknown"  # download_data.get("mime_type", "unknown"),
    content_length: int = -1  # download_data.get("content_length", -1),


def download_uri(uri: str) -> Optional[DownloadResult]:
    logger.info(f"Trying to download {uri}")
    if validate_s3_uri(uri):
        logger.info("URI seems to be an s3 uri")
        return s3_download(uri)
    return http_download(uri)


def http_download(url: str) -> Optional[DownloadResult]:
    logger.info(f"Checking if {url} was already downloaded")
    fn = os.path.basename(urlparse(url).path)
    output_file = os.path.join(output_base_dir, fn)

    # download if the file is not present (preventing unnecessary downloads)
    start_time = time.time()
    if not os.path.exists(output_file):
        logger.info(f"File {output_file} not downloaded yet")
        with open(output_file, "wb") as file:
            response = requests.get(url)
            file.write(response.content)
            file.close()
    download_time = (time.time() - start_time) * 1000  # time in ms
    return DownloadResult(
        output_file,
        download_time,  # TODO add mime_type and content_length
    )


# e.g. s3://dane-asset-staging-gb/assets/2101608170158176431__NOS_JOURNAAL_-WON01513227.mp4
def s3_download(s3_uri: str) -> Optional[DownloadResult]:
    logger.info(f"Checking if {s3_uri} was already downloaded")

    if not validate_s3_uri(s3_uri):
        logger.error(f"Invalid S3 URI: {s3_uri}")
        return None

    # parse S3 URI
    bucket, object_name = parse_s3_uri(s3_uri)
    logger.info(f"OBJECT NAME: {object_name}")
    output_file = os.path.join(
        output_base_dir,
        os.path.basename(object_name),  # i.e. visxp_prep__<source_id>.tar.gz
    )

    if not os.path.exists(output_file):
        # source_id = get_source_id(s3_uri)
        start_time = time.time()
        s3 = S3Store(s3_endpoint_url)
        success = s3.download_file(bucket, object_name, output_base_dir)

        if not success:
            logger.error("Failed to download input data from S3")
            return None
    download_time = time.time() - start_time
    return DownloadResult(
        output_file,
        download_time,
    )
