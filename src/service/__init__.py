from flask import Flask
import api
# from flask_cors import CORS
from flask import send_from_directory, url_for
from app.health_check import HealthCheckProxy


def create_app():
    app = Flask("search")
    app.config["DEBUG"] = True
    # CORS(app)

    app.logger.info("initializing api")
    api.init_app(
        app,
        title="Beeld en Geluid Search API",
        description="Access the various collections hosted in the B&G laboratory",
    )

    @property  # type: ignore
    def specs_url(self):
        app.logger.debug("Entered function")
        return url_for(self.endpoint("specs"), _external=True, _scheme="https")

    @app.route("/robots.txt")
    def static_from_root():
        return send_from_directory(app.static_folder, "robots.txt")

    # wires up the ping and ready check
    HealthCheckProxy(app)

    return app
