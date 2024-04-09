from models import (
    WhisperASRInput,
    WhisperASROutput,
    OutputType,
)
import logging
import time
import json
from dane.config import cfg
from dane.provenance import Provenance
from io_util import (
    get_base_output_dir,
    get_output_file_path,
)
from faster_whisper import WhisperModel


def run_whisper(
    input: WhisperASRInput,
) -> WhisperASROutput:
    logger = logging.getLogger(__name__)
    logger.info("Starting model application")
    start = time.time() * 1000  # convert to ms
    destination = get_output_file_path(input.source_id, OutputType.TRANSCRIPT)

    # float16 only works on GPU, float32 or int8 are recommended for CPU
    model = WhisperModel(
        cfg.WHISPER_ASR_SETTINGS.MODEL_VERSION,
        device=cfg.WHISPER_ASR_SETTINGS.DEVICE,
        compute_type=(
            "float16" if cfg.WHISPER_ASR_SETTINGS.DEVICE == "cuda" else "float32"
        ),
    )

    segments, _ = model.transcribe(
        input.input_file_path,
        vad_filter=cfg.WHISPER_ASR_SETTINGS.VAD,
        beam_size=5,
        best_of=5,
        temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
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
                        "text": word.word.lstrip(),
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
                "text": segment.text.lstrip(),
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
        software_version="0.1.0",
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
