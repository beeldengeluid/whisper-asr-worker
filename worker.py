import logging
import sys
import os
from base_util import validate_config
from dane import Document, Task, Result
from dane.base_classes import base_worker
from dane.config import cfg
from dane.provenance import Provenance
from models import CallbackResponse
from io_util import (
    fetch_input_s3_uri,
    source_id_from_s3_uri,
    get_s3_output_file_uri,
)
from pika.exceptions import ChannelClosedByBroker  # type: ignore
import main_data_processor


logger = logging.getLogger()


class WhisperASRWorker(base_worker):
    def __init__(self, config):
        logger.info(config)

        if not validate_config(config, not self.UNIT_TESTING):
            logger.error("Invalid config, quitting")
            sys.exit()

        self.__queue_name = "QUEUE_NAME"
        self.__binding_key = "#.BINDING_KEY"
        self.__depends_on = (
            list(config.DANE_DEPENDENCIES) if "DANE_DEPENDENCIES" in config else []
        )

        super().__init__(
            self.__queue_name,
            self.__binding_key,
            config,
            self.__depends_on,
            auto_connect=not self.UNIT_TESTING,
            no_api=self.UNIT_TESTING,
        )

        # NOTE: cannot be automatically filled, because no git client is present
        if not self.generator:
            logger.info("Generator was None, creating it now")
            self.generator = {
                "id": "dane-whisper-asr-worker",
                "type": "dane-whisper-asr-worker",
                "name": "ASR using Whisper",
                "homepage": "https://github.com/beeldengeluid/dane-whisper-asr-worker",
            }

    """----------------------------------INTERACTION WITH DANE SERVER ---------------------------------"""

    # DANE callback function, called whenever there is a job for this worker
    def callback(self, task: Task, doc: Document) -> CallbackResponse:
        logger.info("Receiving a task from the DANE server!")
        logger.info(task)
        logger.info(doc)

        # fetch s3 uri of input data:
        s3_uri = fetch_input_s3_uri(self.handler, doc)

        # now run the main process!
        processing_result, full_provenance_chain = main_data_processor.run(s3_uri)

        # if results are fine, save something to the DANE index
        if processing_result.get("state", 500) == 200:
            logger.info(
                "applying IO on output went well, now finally saving to DANE index"
            )
            self.save_to_dane_index(
                doc,
                task,
                get_s3_output_file_uri(source_id_from_s3_uri(s3_uri)),
                provenance=full_provenance_chain,
            )
        return processing_result

    # TODO adapt
    def save_to_dane_index(
        self,
        doc: Document,
        task: Task,
        s3_location: str,
        provenance: Provenance,
    ) -> None:
        logger.info("saving results to DANE, task id={0}".format(task._id))
        # TODO figure out the multiple lines per transcript (refresh my memory)
        r = Result(
            self.generator,
            payload={
                "doc_id": doc._id,
                "task_id": task._id if task else None,
                "doc_target_id": doc.target["id"],
                "doc_target_url": doc.target["url"],
                "s3_location": s3_location,
                "provenance": provenance.to_json(),
            },
            api=self.handler,
        )
        r.save(task._id)


# Start the worker
# passing --run-test-file will run the whole process on the files in cfg.INPUT.TEST_FILES
if __name__ == "__main__":
    from argparse import ArgumentParser
    import json
    from base_util import LOG_FORMAT

    # first read the CLI arguments
    parser = ArgumentParser(description="dane-whisper-asr-worker")
    parser.add_argument(
        "--run-test-file", action="store", dest="run_test_file", default="n", nargs="?"
    )
    parser.add_argument("--log", action="store", dest="loglevel", default="INFO")
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

    # see if the test file must be run
    if args.run_test_file != "n":
        logger.info("Running feature extraction with INPUT.TEST_INPUT_PATH ")
        if cfg.INPUT.TEST_INPUT_PATH:
            processing_result, full_provenance_chain = main_data_processor.run(
                os.path.join(
                    cfg.FILE_SYSTEM.BASE_MOUNT,
                    cfg.FILE_SYSTEM.INPUT_DIR,
                    cfg.INPUT.TEST_INPUT_PATH,
                )
            )
            logger.info("Results after applying desired I/O")
            logger.info(processing_result)
            logger.info("Full provenance chain")
            logger.info(
                json.dumps(full_provenance_chain.to_json(), indent=4, sort_keys=True)
                if full_provenance_chain
                else None
            )
        else:
            logger.error("Please configure an input file in INPUT.TEST_INPUT_FILE")
            sys.exit()
    else:
        logger.info("Starting the worker")
        # start the worker
        w = WhisperASRWorker(cfg)
        try:
            w.run()
        except ChannelClosedByBroker:
            """
            (406, 'PRECONDITION_FAILED - delivery acknowledgement on channel 1 timed out.
            Timeout value used: 1800000 ms.
            This timeout value can be configured, see consumers doc guide to learn more')
            """
            logger.critical(
                "Please increase the consumer_timeout in your RabbitMQ server"
            )
            w.stop()
        except (KeyboardInterrupt, SystemExit):
            w.stop()
