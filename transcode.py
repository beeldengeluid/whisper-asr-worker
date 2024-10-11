from dataclasses import dataclass
import logging
import os
import time

import base_util
from config import data_base_dir

logger = logging.getLogger(__name__)


@dataclass
class TranscodeOutput:
    transcoded_file_path: str
    provenance: dict
    error: str = ""


def try_transcode(input_path, asset_id, extension) -> TranscodeOutput:
    logger.info(
        f"Determining if transcode is required for input_path: {input_path} asset_id: ({asset_id}) extension: ({extension})"
    )
    start_time = time.time()

    provenance = {
        "activity_name": "Transcoding",
        "activity_description": "Checks if input needs transcoding, then transcodes if so",
        "processing_time_ms": -1,
        "start_time_unix": start_time,
        "parameters": [],
        "software_version": "",
        "input_data": input_path,
        "output_data": "",
        "steps": [],
    }

    # if it's already valid audio no transcode necessary
    if _is_audio_file(extension):
        logger.info("No transcode required, input is audio")
        end_time = (time.time() - start_time) * 1000
        provenance["processing_time_ms"] = end_time
        provenance["output_data"] = input_path
        provenance["steps"].append("No transcode required, input is audio")
        return TranscodeOutput(input_path, provenance)

    # if the input format is not supported, fail
    if not _is_transcodable(extension):
        logger.error(f"input with extension {extension} is not transcodable")
        return TranscodeOutput(input_path, dict(), f"Transcode failure: Input with extension {extension} is not transcodable")

    # check if the input file was already transcoded
    transcoded_file_path = os.path.join(data_base_dir, "input", f"{asset_id}.mp3")
    if os.path.exists(transcoded_file_path):
        logger.info("Transcoded file is already available, no new transcode needed")
        end_time = (time.time() - start_time) * 1000
        provenance["processing_time_ms"] = end_time
        provenance["output_data"] = transcoded_file_path
        provenance["steps"].append(
            "Transcoded file is already available, no new transcode needed"
        )
        return TranscodeOutput(transcoded_file_path, provenance)

    # go ahead and transcode the input file
    success = transcode_to_mp3(
        input_path,
        transcoded_file_path,
    )
    if not success:
        logger.error("Running ffmpeg to transcode failed")
        return TranscodeOutput(input_path, dict(), "Running ffmpeg to transcode failed")

    logger.info(
        f"Transcode of {extension} successful, returning: {transcoded_file_path}"
    )
    end_time = (time.time() - start_time) * 1000
    provenance["processing_time_ms"] = end_time
    provenance["output_data"] = transcoded_file_path
    provenance["steps"].append("Transcode successful")
    return TranscodeOutput(transcoded_file_path, provenance)


def transcode_to_mp3(path: str, asr_path: str) -> bool:
    logger.debug(f"Encoding file: {path}")
    cmd = "ffmpeg -y -i {0} {1}".format(path, asr_path)
    return base_util.run_shell_command(cmd)


def _is_audio_file(extension):
    return extension in [".mp3", ".wav"]


def _is_transcodable(extension):
    return extension in [".mov", ".mp4"]
