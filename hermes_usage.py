"""Read real token usage for a Hermes run from Hermes's own state.db.

Hermes records input/output tokens per session as each model call completes,
so this works both after a run finishes and live while it is still running.
Opened read-only; never writes to Hermes's database.
"""

from __future__ import annotations

import os
import re
import sqlite3
from typing import Optional


def hermes_home() -> str:
    return os.environ.get("HERMES_HOME") or os.path.join(
        os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "hermes"
    )


def _default_state_db() -> str:
    return os.path.join(hermes_home(), "state.db")


STATE_DB = os.environ.get("HERMES_STATE_DB") or _default_state_db()

_SESSION_RE = re.compile(r"^\s*Session:\s+(\S+)\s*$", re.MULTILINE)


def parse_session_id(stdout: str) -> Optional[str]:
    match = _SESSION_RE.search(stdout or "")
    return match.group(1) if match else None


def _connect() -> Optional[sqlite3.Connection]:
    if not os.path.isfile(STATE_DB):
        return None
    try:
        uri = "file:" + STATE_DB.replace("\\", "/") + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        return None


def _to_usage(row: Optional[sqlite3.Row]) -> Optional[dict]:
    if row is None:
        return None
    inp = int(row["input_tokens"] or 0)
    out = int(row["output_tokens"] or 0)
    return {
        "session_id": row["id"],
        "input_tokens": inp,
        "output_tokens": out,
        "total_tokens": inp + out,
        "cache_read_tokens": int(row["cache_read_tokens"] or 0),
        "api_calls": int(row["api_call_count"] or 0),
        "model": row["model"],
        "cache_write_tokens": int(row["cache_write_tokens"] or 0),
    }


_COLUMNS = "id, input_tokens, output_tokens, cache_read_tokens, api_call_count, model, cache_write_tokens"


def session_usage(session_id: str) -> Optional[dict]:
    conn = _connect()
    if conn is None:
        return None
    try:
        row = conn.execute(f"SELECT {_COLUMNS} FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return _to_usage(row)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def _first_cli_session_after(started_after: float) -> Optional[dict]:
    # Paperclip runs one job at a time, so the first CLI session that began
    # after we launched hermes is ours.
    conn = _connect()
    if conn is None:
        return None
    try:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM sessions WHERE source = 'cli' AND started_at >= ?"
            " ORDER BY started_at LIMIT 1",
            (started_after,),
        ).fetchone()
        return _to_usage(row)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def find_usage(stdout: str, started_after: float) -> Optional[dict]:
    """Exact session from stdout when hermes printed it, else time-based match."""
    session_id = parse_session_id(stdout)
    if session_id:
        usage = session_usage(session_id)
        if usage:
            return usage
    return _first_cli_session_after(started_after)
