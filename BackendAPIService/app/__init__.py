from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
import logging
import os

from .routes.health import blp
from .routes.devices import blp_devices
from .utils.logging_config import configure_logging
from .db import get_db_collection

# Initialize Flask app
app = Flask(__name__)
app.url_map.strict_slashes = False

# CORS: allow all origins for demo; can be restricted via env CORS_ORIGINS
cors_origins = os.getenv("CORS_ORIGINS", "*")
CORS(app, resources={r"/*": {"origins": cors_origins}})

# API Docs
app.config["API_TITLE"] = "Device Management REST API"
app.config["API_VERSION"] = "1.0.0"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config['OPENAPI_URL_PREFIX'] = '/docs'
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Logging
configure_logging()
logger = logging.getLogger(__name__)
logger.info("App initialization started")

# Register blueprints
api = Api(app)
api.register_blueprint(blp)
app.register_blueprint(blp_devices)

# Startup validation: verify MongoDB configuration at boot
try:
    _client, _collection = get_db_collection()
    logger.info("Startup DB validation succeeded")
except Exception as e:
    # Log but do not crash app import; run will crash if endpoints accessed.
    logger.error("Startup DB validation failed: %s", e)

