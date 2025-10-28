import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

IPV4_REGEX = re.compile(r"^(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)$")

REQUIRED_FIELDS = {"name", "ip_address", "device_type", "location"}
ALLOWED_STATUS = {"online", "offline", "unknown"}
ALLOWED_FIELDS = {"name", "ip_address", "device_type", "location", "status", "last_checked"}

SORTABLE_FIELDS = {"name", "ip_address", "device_type", "location", "status", "last_checked"}

SEARCHABLE_FIELDS = ("name", "ip_address", "device_type", "location")


# PUBLIC_INTERFACE
def is_valid_ipv4(ip: str) -> bool:
    """Validate IPv4 address format."""
    if not isinstance(ip, str):
        return False
    return bool(IPV4_REGEX.match(ip))


# PUBLIC_INTERFACE
def validate_device_payload(payload: Dict[str, Any], partial: bool = False) -> Tuple[bool, Optional[Dict[str, str]], Dict[str, Any]]:
    """Validate a device payload according to application-level schema.
    Returns (valid, errors, sanitized_payload). When partial=True, only validate provided fields."""
    errors: Dict[str, str] = {}
    sanitized: Dict[str, Any] = {}

    if not isinstance(payload, dict):
        return False, {"payload": "Body must be an object"}, {}

    # Enforce only allowed fields to mitigate NoSQL injection via $ operators etc.
    for k, v in payload.items():
        if k not in ALLOWED_FIELDS:
            errors[k] = "Field not allowed"
        else:
            sanitized[k] = v

    if not partial:
        missing = REQUIRED_FIELDS - set(sanitized.keys())
        if missing:
            for m in sorted(missing):
                errors[m] = "Field is required"

    if "ip_address" in sanitized:
        if not is_valid_ipv4(sanitized["ip_address"]):
            errors["ip_address"] = "Must be a valid IPv4 address"

    if "status" in sanitized:
        if sanitized["status"] not in ALLOWED_STATUS:
            errors["status"] = f"Invalid status; must be one of {sorted(ALLOWED_STATUS)}"

    # Normalize last_checked if provided
    if "last_checked" in sanitized:
        lc = sanitized["last_checked"]
        if isinstance(lc, str):
            try:
                sanitized["last_checked"] = datetime.fromisoformat(lc.replace("Z", "+00:00"))
            except Exception:
                errors["last_checked"] = "Invalid datetime format; use ISO 8601"
        elif not isinstance(lc, datetime):
            errors["last_checked"] = "Invalid datetime value"

    return (len(errors) == 0), (None if not errors else errors), sanitized


# PUBLIC_INTERFACE
def sanitize_search_term(term: str) -> str:
    """Sanitize a search term to avoid regex DoS/injection issues by escaping special chars and limiting length."""
    if not isinstance(term, str):
        return ""
    term = term.strip()
    term = term[:128]  # limit length
    # Escape regex special characters
    return re.escape(term)


# PUBLIC_INTERFACE
def safe_sort_field(field: Optional[str]) -> str:
    """Return a whitelisted sort field or default."""
    if field in SORTABLE_FIELDS:
        return field
    return "name"
