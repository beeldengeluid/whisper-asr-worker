from flask import request, url_for
from flask_restx import Namespace, Resource, fields
import logging
import asyncio
from time import time
from asr import run


api = Namespace("Transcribe", description="Transcribe audio file")
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


@api.route("/transcribe", endpoint="Request new audio file transcription")
class TranscriptionEndpoint(Resource):
    @api.marshal_with(transcribe_request)
    def post(self):
        params = request.get_json(force=True)

        # if busy processing something else: refuse
        task = asyncio.current_task()
        if task is not None:
            return {"status": 503, "message": "Busy on another transcription"}
        # if available: spin up processing
        document_id = params["doc_id"]
        processing_id = document_id + str(time)
        task = asyncio.create_task(
            run(
                input_uri=params["location"], output_uri="TODO"
            )  # TODO determine output_uri
        )
        running_transcriptions[processing_id] = task
        response = {
            "processing_id": processing_id,
            "status_handler": url_for(StatusEndpoint, processing_id),
            "message": f"Transciption task created for document {document_id}.",
            "status": 201,
        }
        return response


@api.route("/tasks/<processing_id>", endpoint="Audio file transcription Task")
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
                True
        except KeyError:
            response["message"] = f"Processing id {processing_id} Unknown"
            response["state"] = 404
        return response

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
        return response
