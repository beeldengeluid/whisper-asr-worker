from flask_restx import Api
from apis.whisper_api import api as transcribe_api

apiVersion = "v1.0"
basePath = "/api"
api = Api(version=apiVersion)

api.add_namespace(transcribe_api, path="%s" % basePath)
