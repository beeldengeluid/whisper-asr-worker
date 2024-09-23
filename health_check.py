import logging
import json
from typing import Dict, Any
from flask import Response
import requests


logger = logging.getLogger(f"search.{__name__}")


class HealthCheckProxy:
    def __init__(self, service):
        self.service = service
        self.service.add_url_rule("/ping", view_func=self.ping, methods=["GET"])
        self.service.add_url_rule("/ready", view_func=self.ready, methods=["GET"])

    def ping(self) -> Response:
        logger.debug("Received ping")
        return Response("pong", mimetype="text/plain")

    def ready(self) -> Response:
        logger.debug("Checking availability all external connections")

        connections: dict[str, Dict[str, Any]] = {}
        logger.info(connections)

        return self.check_connections(connections)

    def check_connections(self, connections: Dict[str, Dict[str, Any]]) -> Response:
        logger.info("Checking the following connections")
        logger.debug(connections)
        overall_status = 200
        for c in connections.values():
            logger.debug(c)
            try:
                c["statusCode"] = requests.get(
                    c["connectionUrl"], verify=False, timeout=5
                ).status_code
            except Exception as e:
                logger.exception(
                    f"Unhandled ready check error for {c['connectionUrl']}"
                )
                c["error"] = str(e)
                c["statusCode"] = 502

            if c["statusCode"] < 200 or c["statusCode"] >= 300:
                logger.error(
                    f"Connection {c['connectionUrl']} failed with {c['statusCode']}"
                )
                overall_status = 502

        return Response(
            json.dumps({"status": overall_status}, indent=4, sort_keys=True),
            overall_status,
            mimetype="application/json",
        )
