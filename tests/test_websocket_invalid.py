from websocket import create_connection
import json

def test_ws_invalid_json_returns_error():
    ws = create_connection("ws://localhost:8000/ws/stream")
    ws.send("this-is-not-json")  # text frame
    msg = json.loads(ws.recv())
    assert msg["type"] == "error"
    assert msg["reason"] == "invalid_json"
    ws.close()