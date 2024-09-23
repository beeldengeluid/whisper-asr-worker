<<<<<<< HEAD:src/whisper.py
from .models import (
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
from .io_util import (
    get_base_output_dir,
    get_output_file_path,
    check_model_availability,
    check_pretrained_model_availability,
)
=======
import ast
import json
import logging
import os

>>>>>>> main:whisper.py
import faster_whisper
from config import (
    model_base_dir,
    w_beam_size,
    w_best_of,
    w_device,
    w_model,
    w_temperature,
    w_vad,
    w_word_timestamps,
)
from base_util import get_asset_info
from model_download import check_model_availability


WHISPER_JSON_FILE = "whisper-transcript.json"
logger = logging.getLogger(__name__)


def run_asr(input_path, output_dir) -> bool:
    logger.info(f"Starting ASR on {input_path}")
    logger.info(f"Device used: {w_device}")
    # checking if model needs to be downloaded from HF or not
    model_location = model_base_dir if check_model_availability() else w_model
    model = faster_whisper.WhisperModel(
        model_location,
        device=w_device,
        compute_type=(  # float16 only works on GPU, float32 or int8 are recommended for CPU
            "float16" if w_device == "cuda" else "float32"
        ),
    )
    logger.info("Model loaded, now getting segments")
    segments, _ = model.transcribe(
        input_path,
        vad_filter=w_vad,
        beam_size=w_beam_size,
        best_of=w_best_of,
        temperature=ast.literal_eval(w_temperature),
        language="nl",
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

    return write_whisper_json(transcript, output_dir)


def write_whisper_json(transcript: dict, output_dir: str) -> bool:
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
        return False
    return True
