from typing import Any, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import json

from db import fetchone, execute_nonquery, execute_returning_scalar

app = FastAPI(title="Live Translator API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: production – set to ["https://your-domain"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ISO_Z(dt: datetime | None = None) -> str:
    """Return ISO-8601 UTC timestamp with trailing 'Z' (e.g., 2025-10-17T10:12:34.567Z)."""
    dt = dt or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ---- MODELS ----

class StartSessionIn(BaseModel):
    """Payload to start a translation session."""
    user_id: int = 1
    source_lang: str = "pl"
    target_lang: str = "en"


# ---- REST ENDPOINTS ----

@app.get("/api/health")
def health() -> Dict[str, Any]:
    """
    Lightweight DB health check.
    Returns JSON instead of throwing 500 if DB is down (easier to debug in UI).
    """
    try:
        row = fetchone("SELECT 1 FROM dual")
        ok = bool(row and row[0] == 1)
        return {"status": "ok" if ok else "fail", "db": ok}
    except Exception as e:
        return {"status": "fail", "db": False, "error": str(e)}


@app.post("/api/session/start")
def start_session(payload: StartSessionIn) -> Dict[str, Any]:
    """
    Create a new translation session and return its ID + start timestamp.
    """
    sql = """
    INSERT INTO translation_sessions (user_id, source_lang, target_lang, started_at)
    VALUES (:user_id, :source_lang, :target_lang, SYSTIMESTAMP)
    RETURNING id INTO :out_id
    """
    try:
        new_id = execute_returning_scalar(sql, {
            "user_id": payload.user_id,
            "source_lang": payload.source_lang,
            "target_lang": payload.target_lang
        })
        return {"session_id": new_id, "started_at": ISO_Z()}
    except Exception as e:
        # e.g., FK violation if user_id doesn't exist
        raise HTTPException(status_code=400, detail=f"Cannot start session: {e}")


@app.post("/api/session/finish/{session_id}")
def finish_session(session_id: int) -> Dict[str, Any]:
    """
    Mark a session as finished (sets finished_at).
    """
    execute_nonquery(
        "UPDATE translation_sessions SET finished_at = SYSTIMESTAMP WHERE id = :id",
        {"id": session_id}
    )
    return {"session_id": session_id, "status": "finished"}


@app.get("/api/session/{session_id}")
def get_session(session_id: int) -> Dict[str, Any]:
    """
    Read session details.
    """
    row = fetchone(
        """
        SELECT id, user_id, source_lang, target_lang, started_at, finished_at
        FROM translation_sessions WHERE id = :id
        """,
        {"id": session_id}
    )
    if not row:
        return {"error": "not_found"}
    keys = ["id", "user_id", "source_lang", "target_lang", "started_at", "finished_at"]
    return dict(zip(keys, row))


# ---- WEBSOCKET (testing stub) ----
@app.websocket("/ws/stream")
async def ws_stream(ws: WebSocket) -> None:
    """
    Test WebSocket:
    - Accepts binary frames (e.g., audio chunks) and counts them.
    - Accepts text frames (JSON control messages like {"type":"start"}).
    - Sends back {"type":"echo","frames":N} on every binary frame.
    """
    await ws.accept()
    frames = 0
    try:
        while True:
            msg = await ws.receive()  # can be {"bytes":...} or {"text":...}
            if "bytes" in msg and msg["bytes"] is not None:
                frames += 1
                await ws.send_text(json.dumps({"type": "echo", "frames": frames}))
            elif "text" in msg and msg["text"] is not None:
                try:
                    payload = json.loads(msg["text"])
                    await ws.send_text(json.dumps({"type": "ack", "received": payload}))
                except json.JSONDecodeError:
                    await ws.send_text(json.dumps({"type": "error", "reason": "invalid_json"}))
    except WebSocketDisconnect:
        await ws.close()
    except Exception:
        try:
            await ws.close(code=1011)
        except Exception:
            pass
