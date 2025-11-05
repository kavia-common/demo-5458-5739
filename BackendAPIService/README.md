# BackendAPIService

Device Management REST API using Flask + pymongo with validation, consistent JSON errors, and optional ping utility.

- Runs on port 3001 and serves a demo UI at /
- Requires MongoDB configuration via environment variables
- See .env.example for required variables
- Live API documentation at /docs (OpenAPI/Swagger UI)
- OpenAPI JSON at /openapi.json

## Environment Variables

Create a .env file (or export in your shell) based on `.env.example`:

Required:
- MONGODB_URI: MongoDB connection string (e.g., mongodb://localhost:27017)
- MONGODB_DB: Database name (e.g., devices)
- MONGODB_COLLECTION: Collection name (e.g., devices)

Optional:
- CORS_ORIGINS: Allowed origins for CORS (default: *)
- LOG_LEVEL: Logging level (default: INFO)
- LOG_FILE: Path to a rotating log file (if desired)

## Setup and Run

1) Install dependencies
   pip install -r requirements.txt

2) Configure environment
   - Copy .env.example to .env and fill in values, or export variables directly.

3) Start the service
   python run.py

Service will be available at:
- UI root: http://localhost:3001/
- API docs: http://localhost:3001/docs
- OpenAPI JSON: http://localhost:3001/openapi.json

## API Usage Summary

Devices
- GET /devices
  - Query params:
    - sort: field name (prefix with '-' for descending). Allowed: name, ip_address, device_type, location, status, last_checked
    - search: case-insensitive term across name, ip_address, device_type, location
- POST /devices
  {
    "name": "Router A",
    "ip_address": "192.168.1.10",
    "device_type": "router",
    "location": "Data Center",
    "status": "unknown"
  }

- GET /devices/{id}
- PUT /devices/{id}
  - Any subset of fields; validation enforced
- DELETE /devices/{id}

Ping
- POST /devices/{id}/ping
  Returns:
  { "status": "online" | "offline", "timestamp": "ISO-8601", "error": "optional" }

Errors use a consistent shape:
{ "code": <http_status>, "message": "<summary>", "details": <optional details> }

## Testing

This repo includes pytest-based tests (unit and API with mocked DB):

- tests/test_validators.py
- tests/test_ping.py
- tests/test_devices_api.py

Run:
  pytest -q

Notes:
- Tests mock MongoDB connections and ping behavior; no live DB or ICMP required.

## Notes on OpenAPI

A static `interfaces/openapi.json` is included for reference. The canonical, up-to-date API documentation is served by the running app at /docs and /openapi.json. If discrepancies are observed, prefer the live docs.

