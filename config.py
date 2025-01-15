import os
import validators


def assert_bool(param: str) -> bool:
    value = os.environ.get(param, "y")
    assert value in ["y", "n"], f"Please use y or n for {param}, not |{value}|"
    return value == "y"


def assert_int(param: str, default: int) -> int:
    value = os.environ.get(param, default)
    try:
        return int(value)
    except ValueError:
        assert False, f"Please enter a valid number for {param}, not |{value}|"


# mounting dirs
DATA_BASE_DIR = os.environ.get("DATA_BASE_DIR", "")
MODEL_BASE_DIR = os.environ.get("MODEL_BASE_DIR", "")

# s3 connection param
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "")

# Whisper params
W_WORD_TIMESTAMPS = assert_bool("W_WORD_TIMESTAMPS")
W_VAD = assert_bool("W_VAD")
W_DEVICE = os.environ.get("W_DEVICE", "cuda")
W_MODEL = os.environ.get("W_MODEL", "large-v2")
W_BEAM_SIZE = assert_int("W_BEAM_SIZE", 5)
W_BEST_OF = assert_int("W_BEST_OF", 5)
W_BATCH_SIZE = assert_int("W_BATCH_SIZE", 50)

# Output filenames
WHISPER_JSON_FILE = os.environ.get("WHISPER_JSON_FILE", "whisper-transcript.json")
DAAN_JSON_FILE = os.environ.get("DAAN_JSON_FILE", "daan-es-transcript.json")
PROV_FILENAME = os.environ.get("PROVENANCE_FILENAME", "provenance.json")

assert DATA_BASE_DIR, "Please add DATA_BASE_DIR to your environment"
assert DATA_BASE_DIR not in [".", "/"], "Please enter an absolute, non-root path"
assert os.path.exists(DATA_BASE_DIR), "DATA_BASE_DIR does not exist"

assert MODEL_BASE_DIR, "Please add MODEL_BASE_DIR to your environment"
assert MODEL_BASE_DIR not in [".", "/"], "Please enter an absolute, non-root path"
assert os.path.exists(MODEL_BASE_DIR), "MODEL_BASE_DIR does not exist"

if S3_ENDPOINT_URL:
    assert validators.url(S3_ENDPOINT_URL), "Please enter a valid S3_ENDPOINT_URL"


assert W_DEVICE in ["cuda", "cpu"], "Please use either cuda|cpu for W_DEVICE"
if W_MODEL[0:5] != "s3://" and not validators.url(W_MODEL):
    assert W_MODEL in [
        "tiny",
        "base",
        "small",
        "medium",
        "large",
        "large-v2",
        "large-v3",
    ], "Please use one of: tiny|base|small|medium|large|large-v2|large-v3 for W_MODEL"
