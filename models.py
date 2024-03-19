from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypedDict
from dane.provenance import Provenance


# returned by callback()
class CallbackResponse(TypedDict):
    state: int
    message: str


# These are the types of output this worker (possibly) provides (depending on configuration)
class OutputType(Enum):
    # name of output type, should just have a significant name, no other restrictions
    # (as far as I understand)
    TRANSCRIPT = "transcript"
    PROVENANCE = "provenance"  # produced by provenance.py


@dataclass
class WhisperASRInput:
    state: int  # HTTP status code
    message: str  # error/success message
    source_id: str = ""  # <program ID>__<carrier ID>
    input_file_path: str = ""  # where the audio was downloaded from
    provenance: Optional[Provenance] = None  # mostly: how long did it take to download


@dataclass
class WhisperASROutput:
    state: int  # HTTP status code
    message: str  # error/success message
    output_file_path: str = ""  # where to store the text file
    provenance: Optional[Provenance] = None  # audio extraction provenance
