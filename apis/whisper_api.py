from flask import request, url_for
from flask_restx import Namespace, Resource, fields
import logging
import asyncio
from time import time, sleep
from asr import run


api = Namespace("ASR", description="Transcribe audio file")
logger = logging.getLogger(f"transcribe.{__name__}")

running_transcriptions: dict[str, asyncio.Task] = {}

# FIXME this model is not correct. Swagger cannot render this
transcribe_request = api.model(
    name="TranscribeRequest",
    model={
        "doc_id": fields.String,
        "location": fields.String
    },
)


def dummy_task(sec=60):
    logger.info(f"I'm going to sleep for {sec} seconds")
    sleep(60)
    logger.info("Just woke op")

@api.route("/transcribe")#, endpoint="Request new audio file transcription")
class TranscriptionEndpoint(Resource):
    @api.expect(transcribe_request)
    def post(self):
        params = request.get_json(force=True)

        # if busy processing something else: refuse
        import pdb
        #pdb.set_trace()
        try:
            task = asyncio.current_task()
            if task is not None:
                return {"status": 503, "message": "Busy on another transcription"}
            logger.debug(f"Currently processing {task}")
        except RuntimeError:
            logger.debug("No running event loop")
            pass
        # if available: spin up processing
        document_id = params["doc_id"]
        processing_id = document_id + str(time())
        #pdb.set_trace()

        logger.info(f"Going to start a new task for {document_id}")
        asyncio.run(self.start_task(
            document_id=document_id,
            input_uri=params["location"],
            processing_id=processing_id
        ))
        logger.info(f"Started processing for {document_id}")

        response = {
            "processing_id": processing_id,
            "status_handler": url_for('ASR_status_endpoint', processing_id=processing_id),
            "message": f"Transciption task created for document {document_id}.",
            "state": 201,
        }
        return response, response['state']

    async def start_task(self, document_id, input_uri, processing_id):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(dummy_task(60))
        task = asyncio.create_task(
            dummy_task(60)
            # run(
            #     input_uri=input_uri, output_uri="TODO"
            # )  # TODO determine output_uri
        )
        running_transcriptions[processing_id] = task


@api.route("/task/<processing_id>")
class StatusEndpoint(Resource):

    def get(self, processing_id):
        response = {"processing_id": processing_id, "message": "", "state": 500}
        try:
            task = running_transcriptions[processing_id]
            if task.done():
                callbackresponse = task.result()
                response["message"] = callbackresponse["message"]
                response["state"] = callbackresponse["state"]
                # TODO: Add information: whereabouts of the processing result!
                # NB: need to adjust src/main_data_processor.py
            if task.cancelled() or task.cancelling():
                response["message"] = "Transcription was cancelled"
                response["state"] = 204
            else:
                # other cases
                logger.info("What is the case here?!")
                True
        except KeyError:
            response["message"] = f"Processing id {processing_id} Unknown"
            import pdb
            pdb.set_trace()
            response["state"] = 404
        return response, response['state']

    def delete(self, processing_id):
        try:
            task = running_transcriptions[processing_id]
            task.cancel()
            response = {
                "message": f"Cancelled processing of {processing_id}",
                "state": 202,
            }
        except KeyError:
            response = {
                "message": f"Processing id Unknown: {processing_id}",
                "state": 404,
            }
        return response, response['state']
