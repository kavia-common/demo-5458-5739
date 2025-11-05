import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app import app as flask_app


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeDeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self):
        self.store = {}
        self._id_seq = 1

    def _oid(self):
        # Simple string to simulate ObjectId-like unique ids
        i = self._id_seq
        self._id_seq += 1
        return f"{i:024d}"

    def find(self, query=None):
        query = query or {}
        # naive filter for $or regex
        items = list(self.store.values())
        if query:
            if "$or" in query:
                ors = query["$or"]
                def matches(doc):
                    for cond in ors:
                        for k, v in cond.items():
                            if k in doc and isinstance(v, dict) and "$regex" in v:
                                import re
                                if re.search(v["$regex"], str(doc[k]), re.I):
                                    return True
                    return False
                items = [d for d in items if matches(d)]
        return FakeCursor(items)

    def find_one(self, filt):
        _id = filt.get("_id")
        if _id is None:
            return None
        return self.store.get(str(_id))

    def insert_one(self, doc):
        _id = self._oid()
        d = dict(doc)
        d["_id"] = _id
        self.store[str(_id)] = d
        return FakeInsertResult(_id)

    def find_one_and_update(self, filt, update, return_document=False):
        _id = str(filt.get("_id"))
        d = self.store.get(_id)
        if not d:
            return None
        for k, v in update.get("$set", {}).items():
            d[k] = v
        self.store[_id] = d
        return d

    def update_one(self, filt, update):
        return self.find_one_and_update(filt, update, return_document=True)

    def delete_one(self, filt):
        _id = str(filt.get("_id"))
        existed = _id in self.store
        if existed:
            del self.store[_id]
        return FakeDeleteResult(1 if existed else 0)

    def sort(self, *args, **kwargs):
        return self


class FakeCursor:
    def __init__(self, items):
        self.items = items

    def sort(self, *args, **kwargs):
        # simplified: ignore sort for test purposes
        return self

    def __iter__(self):
        return iter(self.items)


@pytest.fixture(autouse=True)
def app_with_mocked_db(monkeypatch):
    # Patch routes._get_collection to return our fake collection
    import app.routes.devices as devices
    fake = FakeCollection()
    monkeypatch.setattr(devices, "_collection", fake, raising=False)
    monkeypatch.setattr(devices, "_client", SimpleNamespace(close=lambda: None), raising=False)
    # Also ensure call returns fake
    def fake_get_collection():
        return fake
    monkeypatch.setattr(devices, "_get_collection", lambda: fake)
    yield


@pytest.fixture()
def client():
    flask_app.testing = True
    return flask_app.test_client()


def test_list_devices_empty(client):
    res = client.get("/devices")
    assert res.status_code == 200
    assert res.get_json() == []


def test_create_and_get_device(client, monkeypatch):
    payload = {
        "name": "Switch 01",
        "ip_address": "10.0.0.20",
        "device_type": "switch",
        "location": "Rack A",
        "status": "unknown",
    }
    res = client.post("/devices", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 201
    created = res.get_json()
    assert created["name"] == "Switch 01"
    assert "id" in created

    # Get
    gid = created["id"]
    res2 = client.get(f"/devices/{gid}")
    assert res2.status_code == 200
    got = res2.get_json()
    assert got["id"] == gid
    assert got["ip_address"] == "10.0.0.20"


def test_update_device_and_list_search(client):
    # create
    payload = {
        "name": "Router Z",
        "ip_address": "192.168.1.2",
        "device_type": "router",
        "location": "HQ",
        "status": "unknown",
    }
    res = client.post("/devices", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 201
    device = res.get_json()

    # update location
    res2 = client.put(f"/devices/{device['id']}", data=json.dumps({"location": "Branch"}), content_type="application/json")
    assert res2.status_code == 200
    updated = res2.get_json()
    assert updated["location"] == "Branch"

    # list with search
    res3 = client.get("/devices?search=router")
    assert res3.status_code == 200
    arr = res3.get_json()
    assert any(d["name"] == "Router Z" for d in arr)


def test_delete_device(client):
    payload = {
        "name": "AP1",
        "ip_address": "10.10.0.5",
        "device_type": "ap",
        "location": "Lobby",
        "status": "unknown",
    }
    res = client.post("/devices", data=json.dumps(payload), content_type="application/json")
    did = res.get_json()["id"]
    res2 = client.delete(f"/devices/{did}")
    assert res2.status_code == 204
    # second delete -> NotFound
    res3 = client.delete(f"/devices/{did}")
    assert res3.status_code == 404
    body = res3.get_json()
    assert body["code"] == 404


def test_ping_device_updates_status_and_timestamp(client, monkeypatch):
    # create
    payload = {
        "name": "Srv1",
        "ip_address": "10.0.0.30",
        "device_type": "server",
        "location": "DC",
        "status": "unknown",
    }
    res = client.post("/devices", data=json.dumps(payload), content_type="application/json")
    did = res.get_json()["id"]

    # mock ping_host to return online
    import app.routes.devices as devices
    monkeypatch.setattr(devices, "ping_host", lambda ip: ("online", datetime.now(timezone.utc).isoformat(), ""))

    res2 = client.post(f"/devices/{did}/ping")
    assert res2.status_code == 200
    pr = res2.get_json()
    assert pr["status"] == "online"
    assert "timestamp" in pr
