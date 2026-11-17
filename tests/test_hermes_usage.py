import sqlite3

import pytest

import hermes_usage


@pytest.fixture()
def state_db(tmp_path, monkeypatch):
    path = tmp_path / "state.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT, started_at REAL,"
        " input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER,"
        " api_call_count INTEGER, model TEXT, cache_write_tokens INTEGER)"
    )
    conn.executemany(
        "INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)",
        [
            ("old", "cli", 100.0, 5, 5, 0, 1, "grok-4-6", 0),
            ("s1", "cli", 200.0, 52147, 1587, 17361, 3, "grok-4-6", 0),
            ("s2", "cli", 300.0, 10, 2, 0, 1, "grok-4-6", 0),
            ("gw", "telegram", 150.0, 9, 9, 0, 1, "grok-4-6", 0),
        ],
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(hermes_usage, "STATE_DB", str(path))
    return path


def test_parse_session_id_from_stdout():
    out = "...\nResume this session with:\n  hermes --resume 20261115_080350_2aed20\n\nSession:        20261115_080350_2aed20\n"
    assert hermes_usage.parse_session_id(out) == "20261115_080350_2aed20"
    assert hermes_usage.parse_session_id("no session here") is None


def test_usage_by_session_id(state_db):
    u = hermes_usage.session_usage("s1")
    assert u == {"session_id": "s1", "input_tokens": 52147, "output_tokens": 1587,
                 "total_tokens": 53734, "cache_read_tokens": 17361, "api_calls": 3,
                 "model": "grok-4-6", "cache_write_tokens": 0}


def test_usage_falls_back_to_first_cli_session_after_start(state_db):
    u = hermes_usage.find_usage(stdout="", started_after=190.0)
    assert u["session_id"] == "s1"


def test_stdout_session_id_wins_over_time_fallback(state_db):
    u = hermes_usage.find_usage(stdout="Session: s2", started_after=190.0)
    assert u["session_id"] == "s2"


def test_missing_db_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(hermes_usage, "STATE_DB", str(tmp_path / "nope.db"))
    assert hermes_usage.find_usage(stdout="Session: s1", started_after=0) is None


def test_run_hermes_chat_attaches_state_db_usage(monkeypatch):
    import io

    import hermes_runner
    from runner import _from_raw

    class FakeProc:
        pid = 7
        returncode = 0

        def __init__(self, *a, **k):
            self.stdout = io.StringIO("PONG\nSession:        sess-1\n")
            self.stderr = io.StringIO("")

        def poll(self):
            return 0

    seen = {}

    def fake_find_usage(stdout, started_after):
        seen["stdout"] = stdout
        return {"session_id": "sess-1", "input_tokens": 100, "output_tokens": 20,
                "total_tokens": 120, "cache_read_tokens": 0, "api_calls": 1}

    monkeypatch.setattr(hermes_runner, "hermes_available", lambda: (True, "hermes"))
    monkeypatch.setattr(hermes_runner.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(hermes_usage, "find_usage", fake_find_usage)

    raw = hermes_runner.run_hermes_chat("hi")
    assert "Session:        sess-1" in seen["stdout"]
    result = _from_raw(raw, model="grok")
    assert (result.input_tokens, result.output_tokens, result.tokens) == (100, 20, 120)
    assert result.usage_source == "parsed"
