from app import app


def test_root_serves_ui():
    client = app.test_client()
    res = client.get("/")
    assert res.status_code in (200, 308, 301)  # allow redirect behavior if any
