import logging
import os
import time
from urllib.parse import urlparse

from base_util import (
    get_asset_info,
    save_provenance,
)
from config import (
    DATA_BASE_DIR,
    W_WORD_TIMESTAMPS,
    W_DEVICE,
    W_MODEL,
    W_BEAM_SIZE,
    W_BEST_OF,
    W_VAD,
    WHISPER_JSON_FILE,
    DAAN_JSON_FILE,
    PROV_FILENAME,
)

from download import download_uri
from whisper import run_asr
from base_util import remove_all_input_output, transfer_asr_output, Provenance
from transcode import try_transcode
from daan_transcript import generate_daan_transcript

logger = logging.getLogger(__name__)


def run(input_uri: str, output_uri: str, model=None) -> dict:
    logger.info(f"Processing {input_uri} (save to --> {output_uri})")
    start_time = time.time()
    prov_steps = []  # track provenance

    try:
        # 1. get all needed info about input
        fn = os.path.basename(urlparse(input_uri).path)
        asset_id, extension = get_asset_info(fn)
        data_dir = os.path.join(DATA_BASE_DIR, asset_id)

        # 2. download input
        dl_result = download_uri(input_uri, data_dir, fn, extension)
        logger.info(dl_result)

        prov_steps.append(dl_result.provenance)

        # 3. check if the input file is suitable for processing any further
        transcode_prov = try_transcode(
            dl_result.file_path, asset_id, extension, data_dir
        )
        prov_steps.append(transcode_prov)

        # 4. run ASR
        whisper_prov = Provenance(
            activity_name="Whisper transcript already exists",
            activity_description="",
            start_time_unix=time.time(),
            input_data="",
        )

        if not asr_already_done(data_dir):
            logger.info("No Whisper transcript found")
            whisper_prov = run_asr(dl_result.file_path, data_dir, asset_id, model)
        else:
            logger.info(f"Whisper transcript already present in {data_dir}")

        prov_steps.append(whisper_prov)

        # 5. generate DAAN format transcript
        daan_prov = Provenance(
            activity_name="DAAN transcript already exists",
            activity_description="",
            start_time_unix=time.time(),
            input_data="",
        )

        if not daan_transcript_already_done(data_dir):
            logger.info("No DAAN transcript found")
            daan_prov = generate_daan_transcript(data_dir)
        else:
            logger.info(f"DAAN transcript already present in {data_dir}")

        prov_steps.append(daan_prov)

        # 6. generate final provenance
        end_time = (time.time() - start_time) * 1000
        final_prov = Provenance(
            activity_name="Whisper ASR Worker",
            activity_description="Worker that gets a video/audio file as input and outputs JSON transcripts in various formats",
            processing_time_ms=end_time,
            start_time_unix=start_time,
            parameters={
                "WORD_TIMESTAMPS": W_WORD_TIMESTAMPS,
                "DEVICE": W_DEVICE,
                "VAD": W_VAD,
                "MODEL": W_MODEL,
                "BEAM_SIZE": W_BEAM_SIZE,
                "BEST_OF": W_BEST_OF,
            },
            input_data=input_uri,
            output_data=output_uri if output_uri else data_dir,
            steps=prov_steps,
        )

        save_provenance(final_prov, data_dir)

        # 7. transfer output
        if output_uri:
            transfer_asr_output(data_dir, output_uri)
            remove_all_input_output(data_dir)
        else:
            logger.info("No output_uri specified, so all is done")

        return {
            "whisper_transcript": WHISPER_JSON_FILE,
            "daan_transcript": DAAN_JSON_FILE,
            "provenance": PROV_FILENAME
        }

    except Exception as e:
        logger.error(f"Worker failed! Exception raised: {e}")
        # Check if variable exists (might not if exception raised from download_uri)
        if "dl_result" in locals():
            remove_all_input_output(data_dir)
        raise e


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
