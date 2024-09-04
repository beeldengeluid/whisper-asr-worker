import json
import logging
import os
from typing import TypedDict, List, Optional
from whisper import WHISPER_JSON_FILE


# TODO ADAPT FOR WHISPER!
logger = logging.getLogger(__name__)
JSON_FILE = "transcript.json"  # transcript used for indexing


class ParsedResult(TypedDict):
    words: str
    wordTimes: List[int]
    start: float
    sequenceNr: int
    fragmentId: str
    carrierId: str


# asr_output_dir e.g mount/asr-output/1272-128104-0000
# NOTE: only handles Kaldi_NL generated files at this moment
def generate_transcript(asr_output_dir: str) -> bool:
    logger.info(f"Generating transcript from: {asr_output_dir}")
    whisper_transcript = load_whisper_transcript(asr_output_dir)
    if not whisper_transcript:
        logger.error("No whisper_transcript.json found")
        return False

    transcript = parse_whisper_transcript(whisper_transcript)

    # TODO parse the whisper_transcript
    try:
        # write transcript.json
        with open(os.path.join(asr_output_dir, JSON_FILE), "w+", encoding="utf-8") as f:
            logger.info(transcript)
            json.dump(transcript, f, ensure_ascii=False, indent=4)
    except EnvironmentError as e:  # OSError or IOError...
        logger.exception(os.strerror(e.errno))
        return False

    return True


def load_whisper_transcript(asr_output_dir: str) -> Optional[dict]:
    path = os.path.join(asr_output_dir, WHISPER_JSON_FILE)
    try:
        whisper_transcript = json.load(open(path))
    except Exception:
        logger.exception(f"Could not load {path}")
    return whisper_transcript


# TODO implement converting whisper output into elasticsearch index doc format
def parse_whisper_transcript(whisper_transcript: dict):  # -> List[ParsedResult]:
    logger.warning("Not implemented yet, just returning the whisper_transcript.json")
    return whisper_transcript
