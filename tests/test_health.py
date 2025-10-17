import requests

BASE_URL = "http://localhost:8000"

def test_health():
    """Simple API health check"""
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["db"] is True
