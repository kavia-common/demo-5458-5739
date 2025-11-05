from app.utils.validators import is_valid_ipv4, validate_device_payload, sanitize_search_term, safe_sort_field


def test_is_valid_ipv4():
    assert is_valid_ipv4("192.168.0.1")
    assert not is_valid_ipv4("999.999.999.999")
    assert not is_valid_ipv4("abc.def.ghi.jkl")
    assert not is_valid_ipv4(123)  # type: ignore


def test_validate_device_payload_create_valid():
    payload = {
        "name": "Router A",
        "ip_address": "10.0.0.1",
        "device_type": "router",
        "location": "DC",
        "status": "unknown",
        "last_checked": "2024-01-01T00:00:00Z",
    }
    valid, errors, sanitized = validate_device_payload(payload, partial=False)
    assert valid
    assert errors is None
    # last_checked normalized to datetime object
    assert sanitized["status"] == "unknown"
    assert "last_checked" in sanitized


def test_validate_device_payload_missing_required():
    valid, errors, _ = validate_device_payload({"name": "x"}, partial=False)
    assert not valid
    assert "ip_address" in errors
    assert "device_type" in errors
    assert "location" in errors


def test_validate_device_payload_partial_updates():
    valid, errors, sanitized = validate_device_payload({"location": "rack 1"}, partial=True)
    assert valid
    assert errors is None
    assert sanitized["location"] == "rack 1"


def test_validate_device_payload_disallowed_field():
    valid, errors, _ = validate_device_payload({"$where": "1==1"}, partial=True)
    assert not valid
    assert "$where" in errors


def test_sanitize_search_term_limits_and_escapes():
    long = "a" * 1000
    san = sanitize_search_term(long)
    assert len(san) <= 128
    assert sanitize_search_term("a.b") == "a\\.b"


def test_safe_sort_field_whitelist():
    assert safe_sort_field("name") == "name"
    assert safe_sort_field("nonexistent") == "name"
