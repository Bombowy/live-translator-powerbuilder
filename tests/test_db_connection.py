from backend.db import fetchone

def test_fetchone_select_dual():
    """Test SELECT 1 FROM dual"""
    row = fetchone("SELECT 1 FROM dual")
    assert row is not None
    assert row[0] == 1
