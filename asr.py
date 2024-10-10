import logging
import os
import time

from base_util import (
    get_asset_info,
    asr_output_dir,
    save_provenance,
    PROVENANCE_JSON_FILE,
)
from config import (
    s3_endpoint_url,
    w_word_timestamps,
    w_device,
    w_model,
    w_beam_size,
    w_best_of,
    w_vad,
)

from download import download_uri
from whisper import run_asr, WHISPER_JSON_FILE
from s3_util import S3Store, parse_s3_uri
from transcode import try_transcode
from daan_transcript import generate_daan_transcript, DAAN_JSON_FILE

logger = logging.getLogger(__name__)

# Get commit hash and use it as version in prov
version = ""
if os.path.exists("git_commit"):
    with open("git_commit", "r") as f:
        for line in f:
            version = line.strip()


def run(input_uri: str, output_uri: str, model=None) -> bool:
    logger.info(f"Processing {input_uri} (save to --> {output_uri})")
    start_time = time.time()
    prov_steps = []  # track provenance
    # 1. download input
    result = download_uri(input_uri)
    logger.info(result)
    if not result:
        logger.error("Could not obtain input, quitting...")
        return False

    prov_steps.append(result.provenance)

    input_path = result.file_path
    asset_id, extension = get_asset_info(input_path)
    output_path = asr_output_dir(input_path)

    # 2. check if the input file is suitable for processing any further
    transcode_output = try_transcode(input_path, asset_id, extension)
    if not transcode_output:
        logger.error("The transcode failed to yield a valid file to continue with")
        return False
    else:
        input_path = transcode_output.transcoded_file_path
        prov_steps.append(transcode_output.provenance)

    # 3. run ASR
    if not asr_already_done(output_path):
        logger.info("No Whisper transcript found")
        whisper_prov = run_asr(input_path, output_path, model)
        if whisper_prov:
            prov_steps.append(whisper_prov)
    else:
        logger.info(f"Whisper transcript already present in {output_path}")
        provenance = {
            "activity_name": "Whisper transcript already exists",
            "activity_description": "",
            "processing_time_ms": "",
            "start_time_unix": "",
            "parameters": [],
            "software_version": "",
            "input_data": "",
            "output_data": "",
            "steps": [],
        }
        prov_steps.append(provenance)

    # 4. generate JSON transcript
    if not daan_transcript_already_done(output_path):
        logger.info("No DAAN transcript found")
        daan_prov = generate_daan_transcript(output_path)
        if daan_prov:
            prov_steps.append(daan_prov)
        else:
            logger.warning("Could not generate DAAN transcript")
    else:
        logger.info(f"DAAN transcript already present in {output_path}")
        provenance = {
            "activity_name": "DAAN transcript already exists",
            "activity_description": "",
            "processing_time_ms": "",
            "start_time_unix": "",
            "parameters": [],
            "software_version": "",
            "input_data": "",
            "output_data": "",
            "steps": [],
        }
        prov_steps.append(provenance)

    end_time = (time.time() - start_time) * 1000
    final_prov = {
        "activity_name": "Whisper ASR Worker",
        "activity_description": "Worker that gets a video/audio file as input and outputs JSON transcripts in various formats",
        "processing_time_ms": end_time,
        "start_time_unix": start_time,
        "parameters": {
            "word_timestamps": w_word_timestamps,
            "device": w_device,
            "vad": w_vad,
            "model": w_model,
            "beam_size": w_beam_size,
            "best_of": w_best_of,
        },
        "software_version": version,
        "input_data": input_uri,
        "output_data": output_uri if output_uri else output_path,
        "steps": prov_steps,
    }

    prov_success = save_provenance(final_prov, output_path)
    if not prov_success:
        logger.warning("Could not save the provenance")

    # 5. transfer output
    if output_uri:
        transfer_asr_output(output_path, output_uri)
    else:
        logger.info("No output_uri specified, so all is done")

    return True


# if S3 output_uri is supplied transfers data to S3 location
def transfer_asr_output(output_path: str, output_uri: str) -> bool:
    logger.info(f"Transferring {output_path} to S3 (destination={output_uri})")
    if not s3_endpoint_url:
        logger.warning("Transfer to S3 configured without an S3_ENDPOINT_URL!")
        return False

    s3_bucket, s3_folder_in_bucket = parse_s3_uri(output_uri)

    s3 = S3Store(s3_endpoint_url)
    return s3.transfer_to_s3(
        s3_bucket,
        s3_folder_in_bucket,
        [
            os.path.join(output_path, DAAN_JSON_FILE),
            os.path.join(output_path, WHISPER_JSON_FILE),
            os.path.join(output_path, PROVENANCE_JSON_FILE),
        ],
    )


# check if there is a whisper-transcript.json
def asr_already_done(output_dir: str) -> bool:
    whisper_transcript = os.path.join(output_dir, WHISPER_JSON_FILE)
    logger.info(f"Checking existence of {whisper_transcript}")
    return os.path.exists(os.path.join(output_dir, WHISPER_JSON_FILE))


# check if there is a daan-es-transcript.json
def daan_transcript_already_done(output_dir: str) -> bool:
    daan_transcript = os.path.join(output_dir, DAAN_JSON_FILE)
    logger.info(f"Checking existence of {daan_transcript}")
    return os.path.exists(os.path.join(output_dir, DAAN_JSON_FILE))
