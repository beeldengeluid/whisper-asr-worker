from flask_restx import Api, Namespace  # type: ignore

apiVersion = "v1.1"
basePath = "/api/%s" % apiVersion
api = Api(version=apiVersion)


transcribe_api = Namespace("Transcribe", description="Transcribe audio file")

transcribe_response = api.model(
    "TranscribeResponse",
    {
        "task_id": 'this_is_not_a_valid_id'
    })


api.add_namespace(transcribe_api, path="%s/transcribe" % basePath)

