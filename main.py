from api import api
import uvicorn
import logging
import sys
from base_util import LOG_FORMAT
from argparse import ArgumentParser


# initialises the root logger
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,  # configure a stream handler only for now (single handler)
    format=LOG_FORMAT,
)
logger = logging.getLogger()


# Start the worker
if __name__ == "__main__":
    # first read the CLI arguments
    parser = ArgumentParser(description="whisper-asr-worker")
    parser.add_argument("--log", action="store", dest="loglevel", default="INFO")
    parser.add_argument("--port", action="store", dest="port", default="5333")
    args = parser.parse_args()

    # initialises the root logger
    logging.basicConfig(
        stream=sys.stdout,  # configure a stream handler only for now (single handler)
        format=LOG_FORMAT,
    )

    # setting the loglevel
    log_level = args.loglevel.upper()
    logger.setLevel(log_level)
    logger.info(f"Logger initialized (log level: {log_level})")
    logger.info(f"Got the following CMD line arguments: {args}")

    port = int(args.port)
    uvicorn.run(api, port=port, host="0.0.0.0")
