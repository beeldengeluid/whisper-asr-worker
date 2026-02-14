import json
import logging
import os
import time
from typing import TypedDict, List
from base_util import Provenance, write_transcript_to_json
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
    daan_transcript = whisper_json_to_daan_format(whisper_transcript)

    # write daan-es-transcript.json
    write_transcript_to_json(daan_transcript, asr_output_dir, DAAN_JSON_FILE)

    end_time = (time.time() - start_time) * 1000
    provenance = Provenance(
        activity_name="Whisper transcript -> DAAN transcript",
        activity_description="Converts the output of Whisper to the DAAN index format",
        processing_time_ms=end_time,
        start_time_unix=start_time,
        input_data=os.path.join(asr_output_dir, WHISPER_JSON_FILE),
        output_data=os.path.join(asr_output_dir, DAAN_JSON_FILE),
    )
    return provenance


def load_whisper_transcript(asr_output_dir: str) -> dict:
    path = os.path.join(asr_output_dir, WHISPER_JSON_FILE)
    whisper_transcript = json.load(open(path))
    return whisper_transcript


def whisper_json_to_daan_format(whisper_transcript: dict) -> List[ParsedResult]:
    i = 0  # sequenceNr counter
    daan_transcript = []
    for segment in whisper_transcript["segments"]:
        wordTimes = []
        words = []
        for word in segment["words"]:
            wordTimes.append(int(word["start"] * 1000))  # as seen in dane-asr-worker
            words.append(word["text"])

        subtitle: ParsedResult = {
            "wordTimes": wordTimes,
            "sequenceNr": i,
            "start": int(segment["start"] * 1000),  # should be same as wordTimes[0]
            # converts i to a 5-char long string prepended with 0s
            # (similar to kaldi output)
            "fragmentId": f"{i:05d}",
            "words": " ".join(
                words
            ),  # NOTE: segment["text"].split(" ") will not always yield the same amount as wordTimes!,
            "carrierId": whisper_transcript["carrierId"],
        }
        daan_transcript.append(subtitle)
    return daan_transcript
