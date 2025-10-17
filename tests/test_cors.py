import requests

BASE = "http://localhost:8000"

def test_cors_preflight_allows_options():
    headers = {
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    r = requests.options(f"{BASE}/api/session/start", headers=headers, timeout=5)
    # Starlette zwróci 200 lub 204; ważne są nagłówki CORS
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") in ("*", "http://example.com")
    assert "content-type" in r.headers.get("access-control-allow-headers", "").lower()
