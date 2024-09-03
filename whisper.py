# import ast
import json
import logging
import os

import faster_whisper
from config import (
    model_base_dir,
    w_beam_size,
    w_best_of,
    w_device,
    # w_model, TODO handle model download later
    # w_temperature,
    w_vad,
    w_word_timestamps,
)


WHISPER_JSON_FILE = "whisper-transcript.json"
logger = logging.getLogger(__name__)


def run_asr(input_path, output_dir) -> bool:
    logger.info(f"Starting ASR on {input_path}")
    model = faster_whisper.WhisperModel(
        model_base_dir,
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
        # temperatures=ast.literal_eval(w_temperature),
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
    transcript = {"segments": segments_to_add}

    with open(os.path.join(output_dir, WHISPER_JSON_FILE), "w+", encoding="utf-8") as f:
        logger.info(transcript)
        json.dump(transcript, f, ensure_ascii=False, indent=4)

    return True
