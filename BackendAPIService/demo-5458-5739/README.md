# Device Management API (BackendAPIService)

Flask-based REST API for managing network devices with MongoDB (pymongo), including CRUD, searching/sorting, and real-time ping status checks.

Service path: demo-5458-5739/BackendAPIService

Features
- REST endpoints:
  - GET /devices
  - POST /devices
  - GET /devices/{id}
  - PUT /devices/{id}
  - DELETE /devices/{id}
  - POST /devices/{id}/ping
- IPv4 validation and schema enforcement
- MongoDB integration via pymongo
- CORS enabled (configurable)
- Structured errors: { code, message, details? }
- OpenAPI docs available at /docs

Requirements
- Python 3.10+
- MongoDB instance
- Environment variables configured (see .env.example)

Environment Variables
Create a .env file (see BackendAPIService/.env.example) and ensure these variables are present in the process environment:
- MONGODB_URI (required): MongoDB connection string (e.g., mongodb://localhost:27017)
- MONGODB_DB (required): Database name (e.g., devices)
- MONGODB_COLLECTION (required): Collection name (e.g., devices)
- CORS_ORIGINS (optional): Allowed origins for CORS (default: *)
- LOG_LEVEL (optional): Logging level (default: INFO)
- LOG_FILE (optional): Path to log file (rotating)

Run locally
- cd demo-5458-5739/BackendAPIService
- pip install -r requirements.txt
- Export your environment variables (or use a .env manager)
- python run.py
App runs on http://localhost:3001

API Usage Summary
- POST /devices
  Body:
  {
    "name": "Router A",
    "ip_address": "192.168.1.10",
    "device_type": "router",
    "location": "Data Center",
    "status": "unknown"
  }

- GET /devices?sort=-name&search=router
- GET /devices/{id}
- PUT /devices/{id} with any subset of fields, e.g. { "location": "Rack 5" }
- DELETE /devices/{id}
- POST /devices/{id}/ping
  Returns:
  { "status": "online" | "offline", "timestamp": "ISO-8601", "error": "optional" }

Notes
- Input validated for required fields and IPv4 format.
- Search is case-insensitive across name, ip_address, device_type, location.
- Sort supports whitelisted fields; prefix with '-' for descending.

Troubleshooting
- If MongoDB env vars are missing or invalid, startup logs will indicate an error and endpoints will return a 500 on DB operations.
- Ensure your environment can run ICMP ping. The app uses pythonping if available; otherwise falls back to system ping.
