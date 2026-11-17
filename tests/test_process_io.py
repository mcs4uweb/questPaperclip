import sys

import hermes_runner


def test_run_process_drains_large_output_without_deadlock():
    # 2 MB on stdout far exceeds the OS pipe buffer; must not hang.
    code = "import sys; sys.stdout.write('x' * 2_000_000); sys.stderr.write('done')"
    result = hermes_runner.run_process([sys.executable, "-c", code], timeout_sec=30)
    assert result["ok"], result["error"]
    assert len(result["stdout"]) == 2_000_000
    assert result["stderr"] == "done"


def test_run_process_stdin_is_closed():
    # A child that reads stdin must get EOF instead of blocking forever.
    code = "import sys; data = sys.stdin.read(); print('eof' if data == '' else 'data')"
    result = hermes_runner.run_process([sys.executable, "-c", code], timeout_sec=30)
    assert result["ok"], result["error"]
    assert result["stdout"] == "eof"


def test_run_process_timeout_keeps_partial_output():
    code = "import sys, time; print('started', flush=True); time.sleep(60)"
    result = hermes_runner.run_process([sys.executable, "-c", code], timeout_sec=2)
    assert not result["ok"]
    assert result["error"].startswith("timed out")
    assert "started" in result["stdout"]


def test_execute_passes_default_job_timeout(monkeypatch):
    import jobs

    seen = {}

    def fake_run_agent(agent, goal, **kwargs):
        seen["timeout_sec"] = kwargs.get("timeout_sec")
        from runner import Result
        return Result(ok=True, stdout="ok")

    monkeypatch.setattr(jobs, "run_agent", fake_run_agent)
    monkeypatch.setattr(jobs.db, "get_agent", lambda _id: {"id": "a1", "name": "a1"})
    monkeypatch.setattr(jobs.db, "reset_daily_spend_if_needed", lambda _id: None)
    monkeypatch.setattr(jobs.db, "update_agent", lambda *a, **k: None)
    monkeypatch.setattr(jobs.db, "update_job", lambda *a, **k: None)
    monkeypatch.setattr(jobs, "_finish", lambda *a, **k: None)
    jobs._execute({"id": "job-t", "agent_id": "a1", "goal": "g"})
    assert seen["timeout_sec"] == jobs.JOB_TIMEOUT_SEC
    assert jobs.JOB_TIMEOUT_SEC > 0
