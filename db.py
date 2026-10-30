"""SQLite persistence for the Quest Paperclip control plane."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
def _db_path() -> Path:
    override = os.environ.get("PAPERCLIP_DB")
    if override:
        return Path(override)
    return DATA_DIR / "paperclip.db"


# Kept for callers that read db.DB_PATH; re-evaluated via get_db_path().
DB_PATH = DATA_DIR / "paperclip.db"
CHICAGO = ZoneInfo("America/Chicago")
DEFAULT_MONTHLY_CAP = 150.0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chicago_now() -> datetime:
    return datetime.now(CHICAGO)


def chicago_today() -> str:
    return chicago_now().date().isoformat()


def get_db_path() -> Path:
    override = os.environ.get("PAPERCLIP_DB")
    if override:
        return Path(override)
    return DATA_DIR / "paperclip.db"


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
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
              job_id TEXT,
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
        _migrate_agent_usage_columns(conn)
        _migrate_jobs_table(conn)
        _migrate_trace_job_column(conn)
        _seed_if_empty(conn)


def _migrate_trace_job_column(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(traces)").fetchall()}
    if "job_id" not in existing:
        conn.execute("ALTER TABLE traces ADD COLUMN job_id TEXT")


def _migrate_agent_hermes_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(agents)").fetchall()}
    additions = {
        "kind": "TEXT NOT NULL DEFAULT 'hermes'",
        "goal": "TEXT NOT NULL DEFAULT ''",
        "working_dir": "TEXT NOT NULL DEFAULT ''",
        "total_tokens": "INTEGER NOT NULL DEFAULT 0",
        "last_run_summary": "TEXT NOT NULL DEFAULT ''",
        "avatar_color": "TEXT NOT NULL DEFAULT 'bg-indigo-500'",
        "spend_date": "TEXT",
        "monthly_spend": "REAL NOT NULL DEFAULT 0",
        "monthly_cap": "REAL",
        "usage_source": "TEXT NOT NULL DEFAULT 'unknown'",
    }
    for name, decl in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE agents ADD COLUMN {name} {decl}")


def _migrate_agent_usage_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(agents)").fetchall()}
    additions = {
        "spend_date": "TEXT",
        "monthly_spend": "REAL NOT NULL DEFAULT 0",
        "monthly_cap": "REAL",
        "usage_source": "TEXT NOT NULL DEFAULT 'unknown'",
    }
    for name, decl in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE agents ADD COLUMN {name} {decl}")


def _migrate_jobs_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY,
          agent_id TEXT NOT NULL,
          ticket_id TEXT,
          kind TEXT NOT NULL DEFAULT '',
          goal TEXT NOT NULL DEFAULT '',
          cwd TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'queued',
          stdout TEXT NOT NULL DEFAULT '',
          stderr TEXT NOT NULL DEFAULT '',
          error TEXT,
          tokens INTEGER,
          cost REAL,
          latency_ms INTEGER NOT NULL DEFAULT 0,
          usage_source TEXT NOT NULL DEFAULT 'unknown',
          created_at TEXT NOT NULL,
          started_at TEXT,
          finished_at TEXT,
          FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
        """
    )
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    if "usage_source" not in existing:
        conn.execute("ALTER TABLE jobs ADD COLUMN usage_source TEXT NOT NULL DEFAULT 'unknown'")


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
    """Do not insert demo Quest / Video / Market agents."""
    return


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


def delete_agent(agent_id: str) -> bool:
    with get_conn() as conn:
        if not conn.execute("SELECT 1 FROM agents WHERE id = ?", (agent_id,)).fetchone():
            return False
        fallback = conn.execute(
            "SELECT id FROM agents WHERE id != ? ORDER BY name LIMIT 1",
            (agent_id,),
        ).fetchone()
        conn.execute("DELETE FROM traces WHERE agent_id = ?", (agent_id,))
        if fallback:
            conn.execute(
                "UPDATE tickets SET assignee_id = ? WHERE assignee_id = ?",
                (fallback["id"], agent_id),
            )
        else:
            conn.execute("DELETE FROM tickets WHERE assignee_id = ?", (agent_id,))
        conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    return True


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


def create_job(
    *,
    job_id: str,
    agent_id: str,
    kind: str,
    goal: str,
    cwd: str = "",
    ticket_id: Optional[str] = None,
    status: str = "running",
) -> dict[str, Any]:
    created = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (
              id, agent_id, ticket_id, kind, goal, cwd, status,
              stdout, stderr, error, tokens, cost, latency_ms, usage_source,
              created_at, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, '', '', NULL, NULL, NULL, 0, 'unknown', ?, ?, NULL)
            """,
            (job_id, agent_id, ticket_id, kind, goal, cwd or "", status, created, created),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_dict(row)


def finish_job(
    job_id: str,
    *,
    status: str,
    stdout: str = "",
    stderr: str = "",
    error: Optional[str] = None,
    tokens: int = 0,
    cost: float = 0.0,
    latency_ms: int = 0,
    usage_source: str = "unknown",
) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE jobs SET
              status = ?, stdout = ?, stderr = ?, error = ?,
              tokens = ?, cost = ?, latency_ms = ?, usage_source = ?,
              finished_at = ?
            WHERE id = ?
            """,
            (
                status,
                stdout or "",
                stderr or "",
                error,
                tokens,
                cost,
                latency_ms,
                usage_source,
                now_iso(),
                job_id,
            ),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_dict(row) if row else None


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
    job_id: Optional[str] = None,
) -> dict[str, Any]:
    ts = timestamp or now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO traces (
              id, agent_id, agent_name, tool_called, prompt, response,
              latency_ms, token_count, status, timestamp, job_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                job_id,
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


def delete_trace(trace_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM traces WHERE id = ?", (trace_id,))
    return cur.rowcount > 0


def list_traces(limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            WITH linked AS (
              SELECT
                tr.*,
                COALESCE(
                  tr.job_id,
                  -- legacy traces without job_id: match the single closest job by time
                  (
                    SELECT c.id FROM (
                      SELECT j2.id, ABS(
                        strftime('%s', COALESCE(j2.finished_at, j2.created_at))
                        - strftime('%s', tr.timestamp)
                      ) AS gap
                      FROM jobs j2
                      WHERE j2.agent_id = tr.agent_id
                    ) c
                    WHERE c.gap < 300
                    ORDER BY c.gap
                    LIMIT 1
                  )
                ) AS linked_job_id
              FROM traces tr
            )
            SELECT
              t.id, t.agent_id, t.agent_name, t.tool_called, t.prompt,
              t.latency_ms, t.token_count, t.status, t.timestamp,
              t.linked_job_id AS job_id,
              COALESCE(NULLIF(j.stdout, ''), t.response) AS response,
              COALESCE(j.stdout, '') AS job_stdout,
              COALESCE(j.stderr, '') AS job_stderr,
              j.error AS job_error,
              j.status AS job_status,
              j.finished_at AS job_finished_at
            FROM linked t
            LEFT JOIN jobs j ON j.id = t.linked_job_id
            ORDER BY t.timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def reset_daily_spend_if_needed(agent_id: str, today: Optional[str] = None) -> Optional[dict[str, Any]]:
    today = today or chicago_today()
    agent = get_agent(agent_id)
    if not agent:
        return None
    spend_date = agent.get("spend_date")
    if spend_date == today:
        return agent
    fields: dict[str, Any] = {"spend_date": today, "daily_spend": 0}
    if agent.get("status") == "exceeded":
        fields["status"] = "idle"
    return update_agent(agent_id, **fields)


def reset_all_daily_spend_if_needed(today: Optional[str] = None) -> None:
    today = today or chicago_today()
    for agent in list_agents():
        reset_daily_spend_if_needed(agent["id"], today=today)


def get_meta(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    return row["value"]


def set_meta(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_company_monthly_cap() -> float:
    raw = get_meta("monthly_cap")
    if raw is None or raw == "":
        return DEFAULT_MONTHLY_CAP
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_MONTHLY_CAP


def set_company_monthly_cap(value: float) -> float:
    cap = max(0.0, float(value))
    set_meta("monthly_cap", str(cap))
    return cap


def create_job(
    *,
    job_id: str,
    agent_id: str,
    kind: str,
    goal: str,
    cwd: str = "",
    ticket_id: Optional[str] = None,
) -> dict[str, Any]:
    created = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs (
              id, agent_id, ticket_id, kind, goal, cwd, status,
              created_at, usage_source
            ) VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, 'unknown')
            """,
            (job_id, agent_id, ticket_id, kind, goal, cwd or "", created),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_dict(row)


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_dict(row) if row else None


def list_jobs(agent_id: Optional[str] = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE agent_id = ? ORDER BY created_at DESC",
                (agent_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    return [row_to_dict(r) for r in rows]


def list_open_jobs(agent_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE agent_id = ? AND status IN ('queued', 'running') ORDER BY created_at",
            (agent_id,),
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def get_running_job(agent_id: str) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE agent_id = ? AND status = 'running' LIMIT 1",
            (agent_id,),
        ).fetchone()
    return row_to_dict(row) if row else None


def update_job(job_id: str, **fields: Any) -> Optional[dict[str, Any]]:
    if not fields:
        return get_job(job_id)
    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [job_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {assignments} WHERE id = ?", values)
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_dict(row) if row else None


def claim_next_job() -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM jobs
            WHERE status = 'queued'
              AND agent_id NOT IN (SELECT agent_id FROM jobs WHERE status = 'running')
            ORDER BY created_at
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE jobs SET status = 'running', started_at = ? WHERE id = ?",
            (now_iso(), row["id"]),
        )
        claimed = conn.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()
    return row_to_dict(claimed) if claimed else None
