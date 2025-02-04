import logging
import os
import time
from base_util import Provenance, run_shell_command


logger = logging.getLogger(__name__)


def try_transcode(
    input_file: str,
    asset_id: str,
    extension: str,
    output_path: str,
) -> Provenance:
    logger.info(
        f"Determining if transcode is required for input_path: {input_file} asset_id: ({asset_id}) extension: ({extension})"
    )
    start_time = time.time()

    provenance = Provenance(
        activity_name="Transcoding",
        activity_description="Checks if input needs transcoding, then transcodes if so",
        start_time_unix=start_time,
        input_data=input_file,
    )

    output_file = os.path.join(output_path, f"{asset_id}.mp3")

    # check if the input file needs transcoding (or is already transcoded)
    if _is_audio_file(extension) or os.path.exists(output_file):
        logger.info("Input is already audio or has been transcoded")
        provenance.processing_time_ms = (time.time() - start_time) * 1000
        provenance.output_data = output_path
        provenance.steps.append("Input is already audio or has been transcoded")
        return provenance

    # Get output of "ffmpeg -version"
    success, ffmpeg_ver = run_shell_command(["ffmpeg", "-version"])
    if not success:
        raise RuntimeError("Running ffmpeg to extract audio failed")

    # Add only the ffmpeg version number info to prov
    ffmpeg_ver = " ".join(ffmpeg_ver.split()[:3])
    provenance.software_version = ffmpeg_ver

    # if the input format is not supported, fail
    if not _is_transcodable(extension):
        raise ValueError(
            f"Audio extraction failure: Input with extension {extension} is not transcodable"
        )

    # go ahead and transcode the input file
    success = transcode_to_mp3(
        input_file,
        output_file,
    )
    if not success:
        raise RuntimeError("Running ffmpeg to transcode failed")

    logger.info(f"Transcode of {extension} successful, returning: {output_file}")

    provenance.processing_time_ms = (time.time() - start_time) * 1000
    provenance.output_data = output_file
    provenance.steps.append("Transcode successful")
    return provenance


def transcode_to_mp3(path: str, asr_path: str) -> bool:
    logger.debug(f"Encoding file: {path}")
    success, _ = run_shell_command(["ffmpeg", "-y", "-i", path, asr_path])
    return success


def _is_audio_file(extension):
    return extension in [".mp3", ".wav"]


def _is_transcodable(extension):
    return extension in [".mov", ".mp4"]
