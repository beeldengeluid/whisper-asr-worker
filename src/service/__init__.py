from flask import Flask
from .rest_api import api
# from flask_cors import CORS
from flask import url_for, send_from_directory
from .health_check import HealthCheckProxy


def create_app():
    service = Flask("transcribe")
    service.config["DEBUG"] = True
    # CORS(service)

    service.logger.info("initializing api")
    api.init_app(
        service,
        title="Beeld en Geluid Transcription API",
        description="Transcribe an audio file using Whisper ASR",
    )

    @property  # type: ignore
    def specs_url(self):
        service.logger.debug("Entered function")
        return url_for(self.endpoint("specs"), _external=True, _scheme="https")

    @service.route("/robots.txt")
    def static_from_root():
        return send_from_directory(service.static_folder, "robots.txt")

    # wires up the ping and ready check
    HealthCheckProxy(service)

    return service
