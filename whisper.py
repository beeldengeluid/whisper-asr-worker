# import ast
import json
import logging
import os
import time

import faster_whisper

from config import (
    MODEL_BASE_DIR,
    W_BEAM_SIZE,
    W_BEST_OF,
    W_DEVICE,
    W_MODEL,
    W_BATCH_SIZE,
    W_VAD,
    W_WORD_TIMESTAMPS,
    WHISPER_JSON_FILE,
)
from base_util import Provenance
from gpu_measure import GpuMemoryMeasure
from model_download import get_model_location


logger = logging.getLogger(__name__)


# loads the whisper model
def load_model(
    model_base_dir: str, model_type: str, device: str
) -> faster_whisper.BatchedInferencePipeline:
    logger.info(f"Loading Whisper model {model_type} for device: {device}")

    # change HuggingFace dir to where model is downloaded
    os.environ["HF_HOME"] = model_base_dir

    # determine loading locally or have Whisper download from HuggingFace
    model_location = get_model_location(model_base_dir, W_MODEL)

    if model_location == "":
        raise ValueError("Transcribe failure: Model could not be loaded")
    model = faster_whisper.WhisperModel(
        model_location,  # either local path or e.g. large-v2 (means HuggingFace download)
        device=device,
        compute_type=(  # float16 only works on GPU, float32 or int8 are recommended for CPU
            "float16" if device == "cuda" else "float32"
        ),
    )
    batching_model = faster_whisper.BatchedInferencePipeline(model=model)
    logger.info(f"Model loaded from location: {model_location}")
    return batching_model


def run_asr(
    input_path: str,
    output_dir: str,
    asset_id: str,
    model=None,
) -> dict:
    logger.info(f"Starting ASR on {input_path}")
    start_time = time.time()

    if not model:
        logger.info("Model not passed as param, need to obtain it first")
        model = load_model(MODEL_BASE_DIR, W_MODEL, W_DEVICE)
    if W_DEVICE == "cpu":
        logger.warning(f"Device selected is {W_DEVICE}: using a batch size of 1")

    os.environ["PYTORCH_KERNEL_CACHE_PATH"] = MODEL_BASE_DIR
    logger.info("Processing segments")

    if W_DEVICE == "cuda":
        gpu_mem_measure = GpuMemoryMeasure()
        gpu_mem_measure.start_measure_gpu_mem()

    segments, _ = model.transcribe(
        input_path,
        vad_filter=W_VAD,
        beam_size=W_BEAM_SIZE,
        best_of=W_BEST_OF,
        batch_size=W_BATCH_SIZE if W_DEVICE == "cuda" else 1,
        language="nl",  # TODO: experiment without language parameter specified (for programs with foreign speech)
        word_timestamps=W_WORD_TIMESTAMPS,
    )

    segments_to_add = []
    for segment in segments:
        words_to_add = []
        if W_WORD_TIMESTAMPS:
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
    # Also added "carrierId" because the DAAN format requires it
    transcript = {"carrierId": asset_id, "segments": segments_to_add}
    end_time = (time.time() - start_time) * 1000

    if W_DEVICE == "cuda":
        max_mem_usage, gpu_limit = gpu_mem_measure.stop_measure_gpu_mem()
        logger.info(
            "Maximum GPU memory usage: %dMiB / %dMiB (%.2f%%)"
            % (
                max_mem_usage,
                gpu_limit,
                (max_mem_usage / gpu_limit) * 100,
            )
        )
        del gpu_mem_measure

    provenance = Provenance(
        activity_name="Running",
        activity_description="Runs Whisper to transcribe the input audio file",
        processing_time_ms=end_time,
        start_time_unix=start_time,
        input_data=input_path,
        output_data=transcript,
    )

    write_whisper_json(transcript, output_dir)
    return provenance


def write_whisper_json(transcript: dict, output_dir: str):
    logger.info("Writing whisper-transcript.json")

    with open(
        os.path.join(output_dir, WHISPER_JSON_FILE), "w+", encoding="utf-8"
    ) as f:
        logger.debug(transcript)
        json.dump(transcript, f, ensure_ascii=False, indent=4)
