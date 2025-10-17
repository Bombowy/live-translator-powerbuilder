import os
from typing import Any, Dict, List, Optional, Tuple, Union

import oracledb
from dotenv import load_dotenv

# Load environment variables from .env (kept out of Git)
load_dotenv()

# Oracle connection settings (default to local XE pluggable DB)
DSN: str = os.getenv("ORACLE_DSN", "localhost/XEPDB1")
USER: str = os.getenv("ORACLE_USER", "app")
PASS: str = os.getenv("ORACLE_PASS", "app")

# Global connection pool
_pool: Optional[oracledb.ConnectionPool] = None


def get_pool() -> oracledb.ConnectionPool:
    """
    Create (once) and return the global Oracle connection pool.

    Benefits:
      - reuses DB connections (lower latency),
      - better concurrency and stability,
      - thread-safe for ASGI servers.
    """
    global _pool
    if _pool is None:
        print(f"[DB] Creating pool to {DSN} as {USER}")
        _pool = oracledb.create_pool(
            user=USER,
            password=PASS,
            dsn=DSN,
            min=1,
            max=5,
            increment=1,
            homogeneous=True,
            timeout=60,              # idle connection close timeout (sec)
            wait_timeout=30,         # wait for free connection (sec)
            max_lifetime_session=60 * 60 * 4,  # recycle after 4h
        )
    return _pool


def execute_nonquery(
    sql: str,
    params: Optional[Union[Dict[str, Any], Tuple[Any, ...]]] = None,
    commit: bool = True,
) -> int:
    """
    Run INSERT/UPDATE/DELETE (no rows returned).
    Returns number of affected rows.
    """
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.arraysize = 100
            cur.execute(sql, params or {})
            if commit:
                conn.commit()
            return cur.rowcount


def fetchone(
    sql: str,
    params: Optional[Union[Dict[str, Any], Tuple[Any, ...]]] = None,
) -> Optional[Tuple[Any, ...]]:
    """
    Execute a SELECT and fetch exactly one row (tuple) or None.
    """
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.arraysize = 100
            cur.execute(sql, params or {})
            return cur.fetchone()


def fetchall(
    sql: str,
    params: Optional[Union[Dict[str, Any], Tuple[Any, ...]]] = None,
) -> List[Tuple[Any, ...]]:
    """
    Execute a SELECT and fetch all rows (list of tuples).
    """
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.arraysize = 1000
            cur.execute(sql, params or {})
            return cur.fetchall()


def execute_returning_scalar(
    sql: str,
    params: Optional[Union[Dict[str, Any], Tuple[Any, ...]]] = None,
    out_bind_name: str = "out_id",
    out_type: oracledb.DbType = oracledb.NUMBER,
) -> Union[int, str, float]:
    """
    Execute single-row INSERT with `RETURNING <col> INTO :<out_bind_name>`
    and return that single scalar value.

    Handles python-oracledb behavior, where .getvalue() returns a 1-element list.
    Raises ValueError if nothing was returned.
    """
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            out_var = cur.var(out_type)
            binds: Dict[str, Any] = dict(params or {})
            binds[out_bind_name] = out_var

            cur.execute(sql, binds)
            conn.commit()

            val = out_var.getvalue()
            if isinstance(val, list):
                if not val:
                    raise ValueError("RETURNING produced no values")
                val = val[0]
            if val is None:
                raise ValueError("RETURNING returned NULL")


            if out_type is oracledb.NUMBER:
                return int(val)
            return val
