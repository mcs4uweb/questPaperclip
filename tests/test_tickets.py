from tests.conftest import make_agent


def test_put_todo_accepted(client):
    agent = make_agent(client)
    created = client.post(
        "/api/tickets",
        json={"title": "A story", "assignee_id": agent["id"], "status": "todo"},
    )
    assert created.status_code == 200
    ticket_id = created.json()["id"]
    res = client.put(f"/api/tickets/{ticket_id}/status", json={"status": "todo"})
    assert res.status_code == 200
    assert res.json()["status"] == "todo"


def test_put_backlog_rejected(client):
    agent = make_agent(client)
    created = client.post(
        "/api/tickets",
        json={"title": "A story", "assignee_id": agent["id"], "status": "todo"},
    )
    ticket_id = created.json()["id"]
    res = client.put(f"/api/tickets/{ticket_id}/status", json={"status": "backlog"})
    assert res.status_code == 400


def test_create_ticket_rejects_legacy_status(client):
    agent = make_agent(client)
    res = client.post(
        "/api/tickets",
        json={"title": "Legacy", "assignee_id": agent["id"], "status": "completed"},
    )
    assert res.status_code == 400


def test_migrate_legacy_ticket_statuses(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERCLIP_DB", str(tmp_path / "legacy.db"))
    import importlib
    import db

    importlib.reload(db)
    db.init_db()
    with db.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO tickets (id, title, description, assignee_id, priority, status, tokens_used, created_at)
            VALUES ('TCK-900', 'old', '', 'quest', 'P2', 'backlog', 0, ?)
            """,
            (db.now_iso(),),
        )
        conn.execute(
            """
            INSERT INTO tickets (id, title, description, assignee_id, priority, status, tokens_used, created_at)
            VALUES ('TCK-901', 'done-old', '', 'quest', 'P2', 'completed', 0, ?)
            """,
            (db.now_iso(),),
        )
        conn.execute(
            """
            INSERT INTO tickets (id, title, description, assignee_id, priority, status, tokens_used, created_at)
            VALUES ('TCK-902', 'wip', '', 'quest', 'P2', 'in_progress', 0, ?)
            """,
            (db.now_iso(),),
        )
    db.migrate_ticket_statuses()
    rows = {row["id"]: row["status"] for row in db.list_tickets()}
    assert rows["TCK-900"] == "todo"
    assert rows["TCK-901"] == "done"
    assert rows["TCK-902"] == "in-progress"
    leftover = [r for r in db.list_tickets() if r["status"] in {"backlog", "completed", "in_progress"}]
    assert leftover == []
