import os
import validators


def assert_bool(param: str) -> bool:
    value = os.environ.get(param, "y")
    assert value in ["y", "n"], f"Please use y or n for {param}"
    return value == "y"


def assert_int(param: str) -> int:
    value = os.environ.get(param, -1)
    try:
        return int(value)
    except ValueError:
        assert False, f"Please enter a valid number for {param}"


def assert_tuple(param: str) -> str:
    value = os.environ.get(param, "(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)")
    try:
        tuple(eval(value))
        return value
    except ValueError:
        assert (
            False
        ), f"Please enter a valid tuple, e.g. (0.0, 0.2, 0.4, 0.6, 0.8, 1.0), for {param}"


# main input & output params
input_uri = os.environ.get("INPUT_URI", "")
output_uri = os.environ.get("OUTPUT_URI", "")

# mounting dirs
output_base_dir = os.environ.get("OUTPUT_BASE_DIR", "")
model_base_dir = os.environ.get("MODEL_BASE_DIR", "")

# s3 connection params
s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", "")
s3_bucket = os.environ.get("S3_BUCKET", "")
s3_folder_in_bucket = os.environ.get("S3_FOLDER_IN_BUCKET", "")

# Whisper params
w_word_timestamps = assert_bool("W_WORD_TIMESTAMPS")
w_vad = assert_bool("W_VAD")

w_device = os.environ.get("W_DEVICE", "cuda")
w_model = os.environ.get("W_MODEL", "large-v2")

w_beam_size = assert_int("W_BEAM_SIZE")
w_best_of = assert_int("W_BEST_OF")

w_temperature = assert_tuple("W_TEMPERATURE")

# validation for each param
if input_uri:
    if input_uri[0:5] != "s3://":
        assert validators.url(input_uri), "Please provide a valid INPUT_URI"

if output_uri:
    if output_uri[0:5] != "s3://":
        assert validators.url(output_uri), "Please provide a valid OUTPUT_URI"


assert output_base_dir, "Please add OUTPUT_BASE_DIR to your environment"
assert output_base_dir not in [".", "/"], "Please enter an absolute, non-root path"
assert os.path.exists(output_base_dir), "OUTPUT_BASE_DIR does not exist"

assert model_base_dir, "Please add MODEL_BASE_DIR to your environment"
assert model_base_dir not in [".", "/"], "Please enter an absolute, non-root path"
assert os.path.exists(model_base_dir), "MODEL_BASE_DIR does not exist"

if s3_bucket or s3_endpoint_url or s3_folder_in_bucket:
    assert s3_bucket, "Please enter the S3_BUCKET to use"
    assert validators.url(s3_endpoint_url), "Please enter a valid S3_ENDPOINT_URL"
    assert s3_folder_in_bucket, "Please enter a path within the supplied S3 bucket"


assert w_device in ["cuda", "cpu"], "Please use either cuda|cpu for W_DEVICE"
assert w_model in [
    "tiny",
    "base",
    "small",
    "medium",
    "large",
    "large-v2",
    "large-v3",
], "Please use one of: tiny|base|small|medium|large|large-v2|large-v3 for W_MODEL"
