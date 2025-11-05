from flask import Flask, render_template
from flask_cors import CORS
from flask_smorest import Api
import logging
import os

from .routes.health import blp
from .routes.devices import blp_devices
from .utils.logging_config import configure_logging
from .db import get_db_collection

# Initialize Flask app with static mapping for assets folder
# Serve assets under /assets so CSS/JS can be loaded by the root page.
app = Flask(
    __name__,
    static_url_path="/assets",
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "assets"),
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
)
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

# PUBLIC_INTERFACE
@app.get("/", endpoint="root")
def root():
    """Serve the main wireframe UI page.
    Returns:
        HTML: Renders templates/index.html which includes:
          - <link rel="stylesheet" href="/assets/wireframe-1-23-11.css">
          - <script src="/assets/wireframe-1-23-11.js" defer></script>
    """
    return render_template("index.html")

# Startup validation: verify MongoDB configuration at boot
try:
    _client, _collection = get_db_collection()
    logger.info("Startup DB validation succeeded")
except Exception as e:
    # Log but do not crash app import; run will crash if endpoints accessed.
    logger.error("Startup DB validation failed: %s", e)

