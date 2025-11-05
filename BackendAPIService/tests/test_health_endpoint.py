from app import app


def test_health_endpoint_json():
    client = app.test_client()
    res = client.get("/")
    # Expect JSON { "message": "Healthy" } from health blueprint OR 200 HTML if template is served.
    if res.is_json:
        data = res.get_json()
        assert "message" in data
        assert data["message"] == "Healthy"
    else:
        # The root route serves index.html; ensure it is HTML 200 OK to keep UI functional
        assert res.status_code == 200
        assert b"<!DOCTYPE html>" in res.data[:100].upper() or b"<HTML" in res.data[:200].upper()
