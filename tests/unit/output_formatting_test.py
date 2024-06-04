from whisper import output_formatting
import json
from typing import List, NamedTuple, Optional, Iterable
import logging


class MockWord(NamedTuple):
    start: float
    end: float
    word: str
    probability: float


class MockSegment(NamedTuple):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: Optional[List[MockWord]]


def test_output_formatting():
    logger = logging.getLogger("__name__")
    wh_output = json.load(open("unittest_data/input.json"), object_hook=lambda d: MockSegment(**d))
    logger.info(wh_output)
    # wh_output = MockSegment(wh_output["segments"][0])
    final_output = output_formatting(Iterable(wh_output))

    assert final_output == json.loads("unittest_data/assert.json")
