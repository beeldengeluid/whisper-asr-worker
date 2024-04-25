from models import (
    WhisperASRInput,
    WhisperASROutput,
    OutputType,
)
import logging
import time
import json
import ast
from dane.config import cfg
from dane.provenance import Provenance
from io_util import (
    get_base_output_dir,
    get_output_file_path,
)
import faster_whisper
import os


# makes sure the model is available, if not download it from S3, if that fails download from Huggingface
def check_model_availability():
    logger = logging.getLogger(__name__)
    logger.info("Checking if the model is available")
    model_checkpoint_path = ".cache/hub/"
    if os.path.exists(model_checkpoint_path):
        logger.info("Model found, continuing")
        return

    logger.info("Model not found, checking availability in S3")
    if not cfg.INPUT.MODEL:
        logger.error(
            "Incomplete config for downloading the model from S3, please configure: INPUT.MODEL"
        )
        logger.error(
            "Downloading from Huggingface instead"
        )
        return

    download_success = False
    # download_model_from_s3(
    #     cfg.VISXP_EXTRACT.MODEL_BASE_MOUNT,  # download models into this dir
    #     cfg.INPUT.MODEL_CHECKPOINT_S3_URI,  # model checkpoint file is stored here
    #     cfg.INPUT.MODEL_CONFIG_S3_URI,  # model config file is stored here
    #     cfg.INPUT.S3_ENDPOINT_URL,  # the endpoint URL of the S3 host
    # )

    if not download_success:
        logger.error("Could not download models from S3, downloading from Huggingface instead...")
    else:
        logger.info("Model successfully downloaded from S3!")


def run_whisper(
    input: WhisperASRInput,
) -> WhisperASROutput:
    logger = logging.getLogger(__name__)
    logger.info("Starting model application")
    start = time.time() * 1000  # convert to ms
    destination = get_output_file_path(input.source_id, OutputType.TRANSCRIPT)

    os.environ["HF_HOME"] = '.cache'

    # float16 only works on GPU, float32 or int8 are recommended for CPU
    model = faster_whisper.WhisperModel(
        cfg.WHISPER_ASR_SETTINGS.MODEL_VERSION,
        device=cfg.WHISPER_ASR_SETTINGS.DEVICE,
        compute_type=(
            "float16" if cfg.WHISPER_ASR_SETTINGS.DEVICE == "cuda" else "float32"
        ),
    )

    segments, _ = model.transcribe(
        input.input_file_path,
        vad_filter=cfg.WHISPER_ASR_SETTINGS.VAD,
        beam_size=cfg.WHISPER_ASR_SETTINGS.BEAM_SIZE,
        best_of=cfg.WHISPER_ASR_SETTINGS.BEST_OF,
        temperature=ast.literal_eval(cfg.WHISPER_ASR_SETTINGS.TEMPERATURE),
        language="nl",
        word_timestamps=cfg.WHISPER_ASR_SETTINGS.WORD_TIMESTAMPS,
    )

    segments_to_add = []
    for segment in segments:
        words_to_add = []
        if cfg.WHISPER_ASR_SETTINGS.WORD_TIMESTAMPS:
            for word in segment.words:
                words_to_add.append(
                    {
                        "text": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                        "confidence": word.probability,
                    }
                )
        segments_to_add.append(
            {
                "id": segment.id,
                "seek": segment.seek,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "tokens": segment.tokens,
                "temperature": segment.temperature,
                "avg_logprob": segment.avg_logprob,
                "compression_ratio": segment.compression_ratio,
                "no_speech_prob": segment.no_speech_prob,
                "words": words_to_add,
            }
        )
    result = {"segments": segments_to_add}

    with open(destination, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info("Transcription finished, saved at " + destination)

    end = time.time() * 1000  # convert to ms

    model_application_provenance = Provenance(
        activity_name="whisper_asr",
        activity_description="transcribed an audio file using Whisper",
        input_data=input.input_file_path,
        start_time_unix=start,
        parameters=cfg.WHISPER_ASR_SETTINGS,
        software_version=faster_whisper.__version__,
        output_data=destination,
        processing_time_ms=end - start,
    )

    if not model_application_provenance:
        return WhisperASROutput(500, "Failed to apply model")

    return WhisperASROutput(
        200,
        "Succesfully applied model",
        get_base_output_dir(input.source_id),
        model_application_provenance,
    )
