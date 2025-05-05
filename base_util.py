import logging
import os
import subprocess
import json
from urllib.parse import urlparse
from dataclasses import dataclass, field, asdict
from typing import List, Tuple
from config import (
    S3_ENDPOINT_URL,
    PROV_FILENAME,
    WHISPER_JSON_FILE,
    DAAN_JSON_FILE,
)
from s3_util import parse_s3_uri, S3Store


logger = logging.getLogger(__name__)


@dataclass
class Provenance:
    activity_name: str
    activity_description: str
    start_time_unix: float
    input_data: str
    processing_time_ms: float = -1
    parameters: dict = field(default_factory=dict)
    software_version: str = ""
    output_data: str = ""
    steps: list = field(default_factory=list)


# the file name without extension is used as asset ID
def get_asset_info(input_file: str) -> Tuple[str, str]:
    file_name = os.path.basename(input_file)
    asset_id, extension = os.path.splitext(file_name)
    logger.info(f"working with this asset ID {asset_id}")
    return asset_id, extension


def extension_to_mime_type(extension: str) -> str:
    mime_dict = {
        ".mov": "video/quicktime",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }

    return mime_dict.get(extension, "unknown")


# used by asr.py and transcode.py
def run_shell_command(command: List[str]) -> Tuple[bool, str]:
    cmd = " ".join(command)
    logger.info("Executing command:")
    logger.info(cmd)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,  # needed to support file glob
    )

    stdout, stderr = process.communicate()
    logger.debug(stdout)
    logger.error(stderr)
    logger.info(f"Process is done: return code {process.returncode}")
    if process.returncode == 0:
        return True, stdout.decode()
    return False, stderr.decode()


def save_provenance(provenance: Provenance, output_dir: str):
    logger.info(f"Saving provenance to: {output_dir}")
    # write provenance.json
    with open(os.path.join(output_dir, PROV_FILENAME), "w+", encoding="utf-8") as f:
        json.dump(asdict(provenance), f, ensure_ascii=False, indent=4)
        logger.info("Provenance successfully saved!")


def validate_http_uri(http_uri: str) -> bool:
    o = urlparse(http_uri, allow_fragments=False)
    if o.scheme != "http" and o.scheme != "https":
        logger.error(f"Invalid protocol in {http_uri}")
        return False
    if o.path == "":
        logger.error(f"No object_name specified in {http_uri}")
        return False
    return True


def remove_all_input_output(path: str) -> bool:
    try:
        if os.path.exists(path):
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
            os.rmdir(path)
            logger.info("All data has been deleted")
        else:
            logger.warning(f"{path} not found")
            return False
        return True
    except OSError:
        return False


def write_transcript_to_json(transcript, output_dir: str, filename: str):
    logger.info(f"Saving transcript to {filename}")

    with open(os.path.join(output_dir, filename), "w+", encoding="utf-8") as f:
        logger.info(f"writing transcript of length '{len(transcript)}'")
        logger.debug(transcript)
        json.dump(transcript, f, ensure_ascii=False, indent=4)


# if S3 output_uri is supplied transfers data to S3 location
def transfer_asr_output(output_path: str, output_uri: str):
    logger.info(f"Transferring {output_path} to S3 (destination={output_uri})")
    if not S3_ENDPOINT_URL:
        raise Exception("Transfer to S3 configured without an S3_ENDPOINT_URL!")

    s3_bucket, s3_folder_in_bucket = parse_s3_uri(output_uri)

    s3 = S3Store(S3_ENDPOINT_URL)
    return s3.transfer_to_s3(
        s3_bucket,
        s3_folder_in_bucket,
        [
            os.path.join(output_path, DAAN_JSON_FILE),
            os.path.join(output_path, WHISPER_JSON_FILE),
            os.path.join(output_path, PROV_FILENAME),
        ],
    )
