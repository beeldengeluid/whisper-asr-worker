# import ast
import json
import logging
import traceback
import os
import time
from typing import Optional

import faster_whisper

from config import (
    model_base_dir,
    w_beam_size,
    w_best_of,
    w_device,
    w_model,
    w_batch_size,
    w_vad,
    w_word_timestamps,
)
from base_util import get_asset_info
from gpu_measure import GpuMemoryMeasure
from model_download import get_model_location


WHISPER_JSON_FILE = "whisper-transcript.json"
logger = logging.getLogger(__name__)


# loads the whisper model
def load_model(
    model_base_dir: str, model_type: str, device: str
) -> faster_whisper.BatchedInferencePipeline | faster_whisper.WhisperModel:
    logger.info(f"Loading Whisper model {model_type} for device: {device}")

    # change HuggingFace dir to where model is downloaded
    os.environ["HF_HOME"] = model_base_dir

    # determine loading locally or have Whisper download from HuggingFace
    model_location = get_model_location(model_base_dir, w_model)

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


def run_asr(input_path, output_dir, model=None) -> dict | str:
    logger.info(f"Starting ASR on {input_path}")
    start_time = time.time()
    try:
        if not model:
            logger.info("Model not passed as param, need to obtain it first")
            model = load_model(model_base_dir, w_model, w_device)
        if w_device == "cpu":
            logger.warning(f"Device selected is {w_device}: using a batch size of 1")

        os.environ["PYTORCH_KERNEL_CACHE_PATH"] = model_base_dir
        logger.info("Processing segments")

        if w_device == "cuda":
            gpu_mem_measure = GpuMemoryMeasure()
            gpu_mem_measure.start_measure_gpu_mem()

        segments, _ = model.transcribe(
            input_path,
            vad_filter=w_vad,
            beam_size=w_beam_size,
            best_of=w_best_of,
            batch_size=w_batch_size if w_device == "cuda" else 1,
            language="nl",  # TODO: experiment without language parameter specified (for programs with foreign speech)
            word_timestamps=w_word_timestamps,
        )

        segments_to_add = []
        for segment in segments:
            words_to_add = []
            if w_word_timestamps:
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
        asset_id, _ = get_asset_info(input_path)
        # Also added "carrierId" because the DAAN format requires it
        transcript = {"carrierId": asset_id, "segments": segments_to_add}
        end_time = time.time() - start_time

        if w_device == "cuda":
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

        provenance = {
            "activity_name": "Running Whisper",
            "activity_description": "Runs Whisper to transcribe the input audio file",
            "processing_time_ms": end_time,
            "start_time_unix": start_time,
            "parameters": [],
            "software_version": faster_whisper.__version__,
            "input_data": input_path,
            "output_data": transcript,
            "steps": [],
        }

        error = write_whisper_json(transcript, output_dir)
        return error if error else provenance
    except Exception as e:
        logger.exception(str(e))
        return traceback.format_exc()


def write_whisper_json(transcript: dict, output_dir: str) -> Optional[str]:
    logger.info("Writing whisper-transcript.json")
    try:
        if not os.path.exists(output_dir):
            logger.info(f"{output_dir} does not exist, creating it now")
            os.makedirs(output_dir)

        with open(
            os.path.join(output_dir, WHISPER_JSON_FILE), "w+", encoding="utf-8"
        ) as f:
            logger.info(transcript)
            json.dump(transcript, f, ensure_ascii=False, indent=4)
    except EnvironmentError as e:  # OSError or IOError...
        logger.exception(os.strerror(e.errno))
        return traceback.format_exc()
    return None
