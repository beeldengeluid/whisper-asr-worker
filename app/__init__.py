from flask import Flask
from logging.config import dictConfig
from apis import api

# from flask import url_for
from flask_cors import CORS

# from flask_restx import Api as rpapi
from health_check import HealthCheckProxy
from base_util import LOG_FORMAT


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            },
        },
        "loggers": {
            "transcribe": {  # root logger
                "handlers": ["wsgi"],
                "level": "DEBUG",
                "propagate": False,
            },
            "__main__": {  # if __name__ == "__main__"
                "handlers": ["wsgi"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
)


def create_app():
    app = Flask("transcribe")

    # Set Flask-specific config variables (from cfg)
    app.config["DEBUG"] = True
    app.config["CORS_HEADERS"] = "Content-Type"
    app.config["RESTPLUS_VALIDATE"] = False

    CORS(app)

    app.logger.info("initializing api")
    api.init_app(
        app,
        title="Beeld en Geluid transcription API",
        description="Transcription API that uses Whisper for transcribing speech",
    )

    app.logger.info("Initialising server (once)...")

    # making sure the swagger UI shows correctly on HTTPS/HTTP
    # @property  # type: ignore
    # def specs_url(self):
    #     app.logger.debug("Swagger specs_url handling")
    #     return url_for(self.endpoint("specs"), _external=True, _scheme="https")

    # if "FORCE_SWAGGER_JSON_HTTPS" in cfg and cfg["FORCE_SWAGGER_JSON_HTTPS"]:
    #     rpapi.specs_url = specs_url

    # wire up the ping and ready checks
    HealthCheckProxy(app)

    return app
