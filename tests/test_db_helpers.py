from uuid import uuid4
from backend.db import execute_returning_scalar, fetchone, execute_nonquery

def test_execute_returning_scalar_inserts_user_and_returns_id():
    username = f"tmp_user_for_test_{uuid4().hex[:8]}"
    new_id = execute_returning_scalar(
        "INSERT INTO users(username) VALUES(:u) RETURNING id INTO :out_id",
        {"u": username}
    )
    assert isinstance(new_id, int)

    row = fetchone("SELECT username FROM users WHERE id = :id", {"id": new_id})
    assert row and row[0] == username

    # cleanup
    execute_nonquery("DELETE FROM users WHERE id = :id", {"id": new_id})