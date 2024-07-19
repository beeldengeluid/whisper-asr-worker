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
    check_model_availability,
    check_pretrained_model_availability,
)
import faster_whisper


def run_whisper(
    input: WhisperASRInput,
) -> WhisperASROutput:
    logger = logging.getLogger(__name__)
    logger.info("Starting model application")
    start = time.time()
    destination = get_output_file_path(input.source_id, OutputType.TRANSCRIPT)
    model_location = (
        cfg.FILE_SYSTEM.BASE_MOUNT_MODEL
        if check_model_availability()
        else cfg.WHISPER_ASR_SETTINGS.MODEL
    )

    if (
        model_location == cfg.WHISPER_ASR_SETTINGS.MODEL
        and not check_pretrained_model_availability()
    ):
        return WhisperASROutput(
            500,
            "Failed to apply model (WHISPER_ASR_SETTINGS.MODEL not configured correctly)",
        )

    if cfg.WHISPER_ASR_SETTINGS.DEVICE not in ["cuda", "cpu"]:
        return WhisperASROutput(
            500,
            "Failed to apply model (WHISPER_ASR_SETTINGS.DEVICE not configured correctly)",
        )

    # float16 only works on GPU, float32 or int8 are recommended for CPU
    model = faster_whisper.WhisperModel(
        model_location,
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

    model_application_provenance = Provenance(
        activity_name="whisper_asr",
        activity_description="Transcribe an audio file using Whisper",
        input_data=input.input_file_path,
        start_time_unix=start,
        parameters=cfg.WHISPER_ASR_SETTINGS,
        software_version=faster_whisper.__version__,
        output_data=destination,
        processing_time_ms=(time.time() - start) * 1000,
    )

    if not model_application_provenance:
        return WhisperASROutput(500, "Failed to apply model")

    return WhisperASROutput(
        200,
        "Succesfully applied model",
        get_base_output_dir(input.source_id),
        model_application_provenance,
    )
