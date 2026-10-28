"""SQLite persistence for the Quest Paperclip control plane."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "paperclip.db"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS agents (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              role TEXT NOT NULL,
              provider TEXT NOT NULL,
              model TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'idle',
              daily_spend REAL NOT NULL DEFAULT 0,
              daily_cap REAL NOT NULL DEFAULT 10,
              last_heartbeat TEXT,
              reports_to TEXT
            );

            CREATE TABLE IF NOT EXISTS tickets (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              description TEXT NOT NULL DEFAULT '',
              assignee_id TEXT NOT NULL,
              priority TEXT NOT NULL DEFAULT 'Medium',
              status TEXT NOT NULL DEFAULT 'backlog',
              tokens_used INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              FOREIGN KEY (assignee_id) REFERENCES agents(id)
            );

            CREATE TABLE IF NOT EXISTS traces (
              id TEXT PRIMARY KEY,
              agent_id TEXT NOT NULL,
              agent_name TEXT NOT NULL,
              tool_called TEXT NOT NULL,
              prompt TEXT NOT NULL,
              response TEXT NOT NULL,
              latency_ms INTEGER NOT NULL DEFAULT 0,
              token_count INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'Success',
              timestamp TEXT NOT NULL,
              FOREIGN KEY (agent_id) REFERENCES agents(id)
            );

            CREATE TABLE IF NOT EXISTS meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            """
        )
        _migrate_ticket_story_columns(conn)
        _migrate_agent_hermes_columns(conn)
        _seed_if_empty(conn)


def _migrate_agent_hermes_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(agents)").fetchall()}
    additions = {
        "kind": "TEXT NOT NULL DEFAULT 'hermes'",
        "goal": "TEXT NOT NULL DEFAULT ''",
        "working_dir": "TEXT NOT NULL DEFAULT ''",
        "total_tokens": "INTEGER NOT NULL DEFAULT 0",
        "last_run_summary": "TEXT NOT NULL DEFAULT ''",
        "avatar_color": "TEXT NOT NULL DEFAULT 'bg-indigo-500'",
    }
    for name, decl in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE agents ADD COLUMN {name} {decl}")


def _migrate_ticket_story_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(tickets)").fetchall()}
    additions = {
        "story_id": "TEXT",
        "epic": "TEXT NOT NULL DEFAULT ''",
        "sprint": "TEXT NOT NULL DEFAULT ''",
        "as_a": "TEXT NOT NULL DEFAULT ''",
        "i_want": "TEXT NOT NULL DEFAULT ''",
        "so_that": "TEXT NOT NULL DEFAULT ''",
        "blocked_by": "TEXT NOT NULL DEFAULT ''",
        "must_not": "TEXT NOT NULL DEFAULT ''",
        "files_existing": "TEXT NOT NULL DEFAULT ''",
        "files_create": "TEXT NOT NULL DEFAULT ''",
        "acceptance": "TEXT NOT NULL DEFAULT ''",
        "test_plan": "TEXT NOT NULL DEFAULT ''",
        "pr_size": "TEXT NOT NULL DEFAULT 'one concern'",
        "tags": "TEXT NOT NULL DEFAULT 'user-story'",
    }
    for name, decl in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE tickets ADD COLUMN {name} {decl}")


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS n FROM agents").fetchone()["n"]
    if count:
        return

    agents = [
        (
            "quest",
            "Quest",
            "Lead orchestrator",
            "OpenClaw / Bedrock",
            "bedrock/grok-4-6",
            "running",
            0.24,
            15.0,
            None,
            None,
        ),
        (
            "video",
            "Video Pipeline",
            "Math / YouTube render queue",
            "local",
            "video-use + Coqui",
            "idle",
            0.0,
            5.0,
            None,
            "quest",
        ),
        (
            "market",
            "Market Watch",
            "Morning stock health check",
            "web",
            "research",
            "idle",
            0.0,
            3.0,
            None,
            "quest",
        ),
    ]
    conn.executemany(
        """
        INSERT INTO agents (
          id, name, role, provider, model, status,
          daily_spend, daily_cap, last_heartbeat, reports_to
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        agents,
    )

    created = now_iso()
    tickets = [
        (
            "TCK-101",
            "Process leftover video-use inputs",
            "option-trading.txt is still unprocessed in video-use-Coqui\\inputs.",
            "video",
            "High",
            "backlog",
            0,
            created,
        ),
        (
            "TCK-102",
            "Morning stock health check",
            "JEPI, SPYI, JEPQ, QQQI, VIG, SCHD snapshot in Central Time.",
            "market",
            "Medium",
            "assigned",
            0,
            created,
        ),
        (
            "TCK-103",
            "Keep Telegram heartbeats off",
            "Heartbeat target stays none. Real DMs to 8856935268 still allowed.",
            "quest",
            "Low",
            "completed",
            0,
            created,
        ),
    ]
    conn.executemany(
        """
        INSERT INTO tickets (
          id, title, description, assignee_id, priority, status, tokens_used, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        tickets,
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('next_ticket', ?)",
        ("104",),
    )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_agents() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM agents ORDER BY name").fetchall()
    return [row_to_dict(r) for r in rows]


def get_agent(agent_id: str) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    return row_to_dict(row) if row else None


def slugify_agent_id(name: str) -> str:
    raw = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
    while "--" in raw:
        raw = raw.replace("--", "-")
    return raw or "agent"


def create_agent(
    name: str,
    role: str,
    provider: str = "hermes",
    model: str = "hermes",
    daily_cap: float = 5.0,
    reports_to: Optional[str] = None,
    status: str = "idle",
    kind: str = "hermes",
    goal: str = "",
    working_dir: str = "",
    avatar_color: str = "bg-indigo-500",
) -> dict[str, Any]:
    base = slugify_agent_id(name)
    agent_id = base
    with get_conn() as conn:
        n = 2
        while conn.execute("SELECT 1 FROM agents WHERE id = ?", (agent_id,)).fetchone():
            agent_id = f"{base}-{n}"
            n += 1
        conn.execute(
            """
            INSERT INTO agents (
              id, name, role, provider, model, status,
              daily_spend, daily_cap, last_heartbeat, reports_to,
              kind, goal, working_dir, total_tokens, last_run_summary, avatar_color
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, NULL, ?, ?, ?, ?, 0, '', ?)
            """,
            (
                agent_id,
                name.strip(),
                role.strip(),
                provider.strip(),
                model.strip(),
                status,
                daily_cap,
                reports_to or None,
                kind,
                goal,
                working_dir,
                avatar_color,
            ),
        )
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    return row_to_dict(row)


def update_agent(agent_id: str, **fields: Any) -> Optional[dict[str, Any]]:
    if not fields:
        return get_agent(agent_id)
    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [agent_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE agents SET {assignments} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    return row_to_dict(row) if row else None


def list_tickets() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
    return [row_to_dict(r) for r in rows]


def get_ticket(ticket_id: str) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return row_to_dict(row) if row else None


def next_ticket_id() -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'next_ticket'"
        ).fetchone()
        n = int(row["value"]) if row else 104
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('next_ticket', ?)",
            (str(n + 1),),
        )
    return f"TCK-{n}"


def next_story_id() -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = 'next_story'").fetchone()
        n = int(row["value"]) if row else 1
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('next_story', ?)",
            (str(n + 1),),
        )
    return f"US-{n}"


def create_ticket(
    title: str,
    description: str,
    assignee_id: str,
    priority: str,
    status: str = "todo",
    story_id: Optional[str] = None,
    epic: str = "",
    sprint: str = "",
    as_a: str = "",
    i_want: str = "",
    so_that: str = "",
    blocked_by: str = "",
    must_not: str = "",
    files_existing: str = "",
    files_create: str = "",
    acceptance: str = "",
    test_plan: str = "",
    pr_size: str = "one concern",
    tags: str = "user-story",
) -> dict[str, Any]:
    ticket_id = next_ticket_id()
    created = now_iso()
    if not story_id:
        story_id = next_story_id()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO tickets (
              id, title, description, assignee_id, priority, status, tokens_used, created_at,
              story_id, epic, sprint, as_a, i_want, so_that, blocked_by, must_not,
              files_existing, files_create, acceptance, test_plan, pr_size, tags
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                title,
                description,
                assignee_id,
                priority,
                status,
                created,
                story_id,
                epic,
                sprint,
                as_a,
                i_want,
                so_that,
                blocked_by,
                must_not,
                files_existing,
                files_create,
                acceptance,
                test_plan,
                pr_size,
                tags,
            ),
        )
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return row_to_dict(row)


def update_ticket(ticket_id: str, **fields: Any) -> Optional[dict[str, Any]]:
    if not fields:
        return get_ticket(ticket_id)
    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [ticket_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE tickets SET {assignments} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return row_to_dict(row) if row else None


def delete_ticket(ticket_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    return cur.rowcount > 0


def add_trace(
    *,
    trace_id: str,
    agent_id: str,
    agent_name: str,
    tool_called: str,
    prompt: str,
    response: str,
    latency_ms: int = 0,
    token_count: int = 0,
    status: str = "Success",
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    ts = timestamp or now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO traces (
              id, agent_id, agent_name, tool_called, prompt, response,
              latency_ms, token_count, status, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                agent_id,
                agent_name,
                tool_called,
                prompt,
                response,
                latency_ms,
                token_count,
                status,
                ts,
            ),
        )
        conn.execute(
            """
            DELETE FROM traces WHERE id NOT IN (
              SELECT id FROM traces ORDER BY timestamp DESC LIMIT 200
            )
            """
        )
        row = conn.execute("SELECT * FROM traces WHERE id = ?", (trace_id,)).fetchone()
    return row_to_dict(row)


def list_traces(limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM traces ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [row_to_dict(r) for r in rows]
