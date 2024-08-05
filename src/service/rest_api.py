from flask_restx import Api  # type: ignore

apiVersion = "v1.1"
basePath = "/api/%s" % apiVersion
api = Api(version=apiVersion)
