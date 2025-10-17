import requests
from backend.db import fetchone, execute_returning_scalar

BASE = "http://localhost:8000"

def ensure_demo_user() -> int:
    row = fetchone("SELECT id FROM users WHERE username = :u", {"u": "demo"})
    if row:
        return int(row[0])
    return execute_returning_scalar(
        "INSERT INTO users(username) VALUES(:u) RETURNING id INTO :out_id",
        {"u": "demo"}
    )

def test_session_lifecycle():
    user_id = ensure_demo_user()

    # start
    start = requests.post(
        f"{BASE}/api/session/start",
        json={"user_id": user_id, "source_lang": "pl", "target_lang": "en"},
        timeout=5,
    )
    print("DEBUG start:", start.status_code, start.text)
    assert start.status_code == 200, start.text
    data = start.json()
    sid = data["session_id"]

    # get
    r = requests.get(f"{BASE}/api/session/{sid}", timeout=5)
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["id"] == sid
    assert s["user_id"] == user_id

    # finish
    fin = requests.post(f"{BASE}/api/session/finish/{sid}", timeout=5)
    assert fin.status_code == 200, fin.text
    assert fin.json()["status"] == "finished"

    # get again
    r2 = requests.get(f"{BASE}/api/session/{sid}", timeout=5)
    assert r2.status_code == 200, r2.text
    assert r2.json()["finished_at"] is not None

def test_session_start_fk_violation_returns_400():
    res = requests.post(
        f"{BASE}/api/session/start",
        json={"user_id": 999999, "source_lang": "pl", "target_lang": "en"},
        timeout=5,
    )
    assert res.status_code == 400
    data = res.json()
    assert "Cannot start session:" in data["detail"]