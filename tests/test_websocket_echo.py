from websocket import create_connection
import json, time

def test_websocket_echo():
    """Test WebSocket echo and ack"""
    ws = create_connection("ws://localhost:8000/ws/stream")
    ws.send(json.dumps({"type": "start", "session_id": 1}))
    ack = json.loads(ws.recv())
    assert ack["type"] == "ack"

    ws.send_binary(b"\x00\x01\x02")
    echo = json.loads(ws.recv())
    assert echo["type"] == "echo"
    assert echo["frames"] >= 1

    ws.close()
