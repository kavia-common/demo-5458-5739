import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from flask import Blueprint, jsonify, request
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from ..db import get_db_collection
from ..utils.errors import BadRequest, NotFound, InternalServerError
from ..utils.ping import ping_host
from ..utils.validators import (
    validate_device_payload,
    sanitize_search_term,
    safe_sort_field,
    SEARCHABLE_FIELDS,
)

blp_devices = Blueprint("devices", __name__, url_prefix="/devices")
logger = logging.getLogger(__name__)

_client = None
_collection: Optional[Collection] = None


def _get_collection() -> Collection:
    """Internal lazy init for Mongo collection."""
    global _client, _collection
    if _collection is None:
        _client, _collection = get_db_collection()
    return _collection


def _serialize_device(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Transform MongoDB document to API-friendly shape."""
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    # Convert last_checked to ISO 8601
    lc = doc.get("last_checked")
    if isinstance(lc, datetime):
        doc["last_checked"] = lc.astimezone(timezone.utc).isoformat()
    return doc


@blp_devices.route("", methods=["GET"])
def list_devices():
    """List devices with optional search and sort.
    Query params:
      - sort: field name, optional; default 'name'. Prefix '-' for descending.
      - search: term, optional; matches across name, ip_address, device_type, location (case-insensitive).
    Returns: JSON array of devices."""
    try:
        coll = _get_collection()
        sort_param = (request.args.get("sort", "name") or "name").strip()
        direction = ASCENDING
        if sort_param.startswith("-"):
            direction = DESCENDING
            sort_field = safe_sort_field(sort_param[1:])
        else:
            sort_field = safe_sort_field(sort_param)

        search = (request.args.get("search", "") or "").strip()
        query: Dict[str, Any] = {}
        if search:
            term = sanitize_search_term(search)
            # case-insensitive regex search on whitelisted fields
            ors = [{f: {"$regex": term, "$options": "i"}} for f in SEARCHABLE_FIELDS]
            query = {"$or": ors}

        cursor = coll.find(query).sort(sort_field, direction)
        items = [_serialize_device(d) for d in cursor]
        return jsonify(items), 200
    except PyMongoError as e:
        logger.exception("Database error during list")
        return InternalServerError(message="Database error", details=str(e)).to_response()


@blp_devices.route("", methods=["POST"])
def create_device():
    """Create a new device. Validates payload and returns created device."""
    try:
        payload = request.get_json(silent=True)
        if payload is None:
            return BadRequest(message="Request body must be JSON").to_response()
        valid, errors, sanitized = validate_device_payload(payload, partial=False)
        if not valid:
            return BadRequest(message="Validation failed", details=errors).to_response()

        # Default values
        sanitized.setdefault("status", "unknown")
        if "last_checked" not in sanitized:
            sanitized["last_checked"] = None

        coll = _get_collection()
        res = coll.insert_one(sanitized)
        inserted = coll.find_one({"_id": res.inserted_id})
        return jsonify(_serialize_device(inserted)), 201
    except PyMongoError as e:
        logger.exception("Database error during create")
        return InternalServerError(message="Database error", details=str(e)).to_response()


@blp_devices.route("/<id>", methods=["GET"])
def get_device(id: str):
    """Get device by ID."""
    try:
        try:
            oid = ObjectId(id)
        except Exception:
            return NotFound(message="Device not found").to_response()

        coll = _get_collection()
        doc = coll.find_one({"_id": oid})
        if not doc:
            return NotFound(message="Device not found").to_response()
        return jsonify(_serialize_device(doc)), 200
    except PyMongoError as e:
        logger.exception("Database error during get")
        return InternalServerError(message="Database error", details=str(e)).to_response()


@blp_devices.route("/<id>", methods=["PUT"])
def update_device(id: str):
    """Update an existing device by ID. Validates payload and returns updated device."""
    try:
        try:
            oid = ObjectId(id)
        except Exception:
            return NotFound(message="Device not found").to_response()

        payload = request.get_json(silent=True)
        if payload is None:
            return BadRequest(message="Request body must be JSON").to_response()

        valid, errors, sanitized = validate_device_payload(payload, partial=True)
        if not valid:
            return BadRequest(message="Validation failed", details=errors).to_response()
        if not sanitized:
            return BadRequest(message="No valid fields to update").to_response()

        # Never allow updating _id
        sanitized.pop("_id", None)

        coll = _get_collection()
        res = coll.find_one_and_update({"_id": oid}, {"$set": sanitized}, return_document=True)
        if not res:
            return NotFound(message="Device not found").to_response()
        updated = coll.find_one({"_id": oid})
        return jsonify(_serialize_device(updated)), 200
    except PyMongoError as e:
        logger.exception("Database error during update")
        return InternalServerError(message="Database error", details=str(e)).to_response()


@blp_devices.route("/<id>", methods=["DELETE"])
def delete_device(id: str):
    """Delete a device by ID."""
    try:
        try:
            oid = ObjectId(id)
        except Exception:
            return NotFound(message="Device not found").to_response()
        coll = _get_collection()
        res = coll.delete_one({"_id": oid})
        if res.deleted_count == 0:
            return NotFound(message="Device not found").to_response()
        return "", 204
    except PyMongoError as e:
        logger.exception("Database error during delete")
        return InternalServerError(message="Database error", details=str(e)).to_response()


@blp_devices.route("/<id>/ping", methods=["POST"])
def ping_device(id: str):
    """Ping a device by ID, update its status and last_checked atomically, and return the result."""
    try:
        try:
            oid = ObjectId(id)
        except Exception:
            return NotFound(message="Device not found").to_response()
        coll = _get_collection()
        doc = coll.find_one({"_id": oid})
        if not doc:
            return NotFound(message="Device not found").to_response()

        ip = doc.get("ip_address")
        status, ts, error = ping_host(ip)
        # Update document
        try:
            ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            ts_dt = datetime.now(timezone.utc)
        update = {"status": status, "last_checked": ts_dt}
        coll.update_one({"_id": oid}, {"$set": update})

        resp = {"status": status, "timestamp": ts}
        if error:
            resp["error"] = error
        return jsonify(resp), 200
    except PyMongoError as e:
        logger.exception("Database error during ping")
        return InternalServerError(message="Database error", details=str(e)).to_response()
