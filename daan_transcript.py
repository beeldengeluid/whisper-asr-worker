import json
import logging
import os
import time
from typing import TypedDict, List
from base_util import Provenance
from config import WHISPER_JSON_FILE, DAAN_JSON_FILE


logger = logging.getLogger(__name__)


class ParsedResult(TypedDict):
    words: str
    wordTimes: List[int]
    start: float
    sequenceNr: int
    fragmentId: str
    carrierId: str


# asr_output_dir e.g /data/output/whisper-test/
def generate_daan_transcript(asr_output_dir: str) -> Provenance:
    logger.info(f"Generating transcript from: {asr_output_dir}")
    start_time = time.time()
    whisper_transcript = load_whisper_transcript(asr_output_dir)
    daan_transcript = parse_whisper_transcript(whisper_transcript)

    # write daan-es-transcript.json
    with open(
        os.path.join(asr_output_dir, DAAN_JSON_FILE), "w+", encoding="utf-8"
    ) as f:
        logger.info(f"writing transcript of length '{len(daan_transcript)}'")
        logger.debug(daan_transcript)
        json.dump(daan_transcript, f, ensure_ascii=False, indent=4)

    end_time = (time.time() - start_time) * 1000
    provenance = Provenance(
        activity_name="Whisper transcript -> DAAN transcript",
        activity_description="Converts the output of Whisper to the DAAN index format",
        processing_time_ms=end_time,
        start_time_unix=start_time,
        input_data=whisper_transcript,
        output_data=daan_transcript,
    )
    return provenance


def load_whisper_transcript(asr_output_dir: str) -> dict:
    path = os.path.join(asr_output_dir, WHISPER_JSON_FILE)
    whisper_transcript = json.load(open(path))
    return whisper_transcript


def parse_whisper_transcript(whisper_transcript: dict) -> List[ParsedResult]:
    i = 0  # sequenceNr counter
    daan_transcript = []
    for segment in whisper_transcript["segments"]:
        wordTimes = []
        for word in segment["words"]:
            wordTimes.append(int(word["start"] * 1000))  # as seen in dane-asr-worker

        subtitle: ParsedResult = {
            "wordTimes": wordTimes,
            "sequenceNr": i,
            "start": segment["start"],
            # converts i to a 5-char long string prepended with 0s
            # (similar to kaldi output)
            "fragmentId": f"{i:05d}",
            "words": segment["text"],
            "carrierId": whisper_transcript["carrierId"],
        }
        daan_transcript.append(subtitle)
    return daan_transcript
