from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ingest_valid_payload():
    payload = {
        "household_id": "ZZZZZZZZZZ",
        "meter_point_id": 9999999999999,
        "consumption": [
            {
                "consumption_type": "Import",
                "consumption_value": 1.5,
                "consumption_date": "2025-01-01",
            }
        ],
    }

    r = client.post("/ingest", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "stored"


def test_ingest_invalid_household_id():
    payload = {
        "household_id": "SHORT",
        "meter_point_id": 9999999999999,
        "consumption": [
            {
                "consumption_type": "Import",
                "consumption_value": 1.5,
                "consumption_date": "2025-01-01",
            }
        ],
    }

    r = client.post("/ingest", json=payload)
    assert r.status_code == 422


def test_statistics_not_found():
    r = client.get("/statistics/household/DOESNOTEXIST")
    assert r.status_code == 404


def test_consumption_pagination():
    r = client.get("/consumption?limit=1&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert body["limit"] == 1
