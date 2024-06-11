from whisper import output_formatting
import json
from typing import List, NamedTuple, Optional
from munch import Munch


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
    wh_json1 = json.load(open("unittest_data/input_1segment.json"))
    wh_json2 = json.load(open("unittest_data/input_1word.json"))
    wh_json3 = json.load(open("unittest_data/input_multisegments.json"))

    wh_output1 = Munch.fromDict(wh_json1)
    wh_output2 = Munch.fromDict(wh_json2)
    wh_output3 = Munch.fromDict(wh_json3)
    final_output1 = output_formatting(wh_output1)
    final_output2 = output_formatting(wh_output2)
    final_output3 = output_formatting(wh_output3)

    assert final_output1 == json.load(open("unittest_data/assert_1segment.json"))
    assert final_output2 == json.load(open("unittest_data/assert_1word.json"))
    assert final_output3 == json.load(open("unittest_data/assert_multisegments.json"))
