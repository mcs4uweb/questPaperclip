"""Isolated FastAPI client against a temp SQLite file."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPERCLIP_DB", str(tmp_path / "paperclip-test.db"))

    import db
    import jobs
    import main
    import runner
    from runner import Result, set_runner_impl

    def fake_run(agent, goal, cwd=None, timeout_sec=None, job_id=None, url=None):
        if "SLEEP" in (goal or ""):
            for _ in range(50):
                if job_id and jobs.is_cancel_requested(job_id):
                    return Result(ok=False, error="cancelled", usage_source="unknown")
                time.sleep(0.1)
            return Result(ok=True, stdout="slept", tokens=1, cost=0.0, usage_source="parsed")
        if "FAIL" in (goal or ""):
            return Result(ok=False, error="failed", stderr="fail", usage_source="unknown")
        if "NOUSAGE" in (goal or ""):
            return Result(ok=True, stdout="done with no footer", usage_source="unknown")
        return Result(
            ok=True,
            stdout="hello from fake",
            tokens=12,
            cost=0.02,
            latency_ms=3,
            model="fake",
            usage_source="parsed",
        )

    set_runner_impl(fake_run)
    db.init_db()
    jobs.start_worker()

    from fastapi.testclient import TestClient

    with TestClient(main.app) as test_client:
        yield test_client

    set_runner_impl(None)


def wait_job(client, job_id: str, timeout: float = 6.0) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        res = client.get(f"/api/jobs/{job_id}")
        assert res.status_code == 200, res.text
        last = res.json()
        if last["status"] in {"succeeded", "failed", "cancelled"}:
            return last
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish: {last}")


def make_agent(client, **overrides) -> dict:
    body = {
        "name": overrides.pop("name", "Worker"),
        "role": overrides.pop("role", "Test runner"),
        "kind": overrides.pop("kind", "hermes"),
        "provider": overrides.pop("provider", "hermes"),
        "model": overrides.pop("model", "fake"),
        "goal": overrides.pop("goal", "do the thing"),
        "daily_cap": overrides.pop("daily_cap", 10.0),
        "status": overrides.pop("status", "idle"),
    }
    body.update(overrides)
    res = client.post("/api/agents", json=body)
    assert res.status_code == 200, res.text
    return res.json()
