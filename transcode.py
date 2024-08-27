import logging
import os
from typing import Optional

import base_util
from base_util import output_base_dir

logger = logging.getLogger(__name__)


def try_transcode(input_path, asset_id, extension) -> Optional[str]:
    logger.info(
        f"Determining if transcode is required for input_path: {input_path} asset_id: ({asset_id}) extension: ({extension})"
    )

    # if it's alrady valid audio no transcode necessary
    if _is_audio_file(extension):
        logger.info("No transcode required, input is audio")
        return input_path

    # if the input format is not supported, fail
    if not _is_transcodable(extension):
        logger.error(f"input with extension {extension} is not transcodable")
        return None

    # check if the input file was already transcoded
    transcoded_file_path = os.path.join(output_base_dir, f"{asset_id}.mp3")
    if os.path.exists(transcoded_file_path):
        logger.info("Transcoded file is already available, no new transcode needed")
        return transcoded_file_path

    # go ahead and transcode the input file
    success = transcode_to_mp3(
        input_path,
        transcoded_file_path,
    )
    if not success:
        logger.error("Transcode failed")
        return None

    logger.info(
        f"Transcode of {extension} successful, returning: {transcoded_file_path}"
    )

    return transcoded_file_path


def transcode_to_mp3(path: str, asr_path: str) -> bool:
    logger.debug(f"Encoding file: {path}")
    cmd = "ffmpeg -y -i {0} {1}".format(path, asr_path)
    return base_util.run_shell_command(cmd)


def _is_audio_file(extension):
    return extension in [".mp3", ".wav"]


def _is_transcodable(extension):
    return extension in [".mov", ".mp4", ".m4a", ".3gp", ".3g2", ".mj2"]
