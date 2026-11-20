from runner import Result, apply_result, run_agent


def test_result_ok_mapping():
    result = Result(ok=True, stdout="done", tokens=10, cost=0.01, latency_ms=5, model="m")
    mapped = apply_result(result)
    assert mapped["ok"] is True
    assert mapped["stdout"] == "done"
    assert mapped["tokens"] == 10
    assert mapped["error"] is None


def test_result_fail_mapping():
    result = Result(ok=False, error="boom", stderr="nope")
    mapped = apply_result(result)
    assert mapped["ok"] is False
    assert mapped["error"] == "boom"
    assert mapped["stderr"] == "nope"


def test_result_empty_stdout_is_not_invented_success_text():
    result = Result(ok=True, stdout="")
    mapped = apply_result(result)
    assert mapped["ok"] is True
    assert mapped["stdout"] == ""


def test_openclaw_unparseable_output_is_readable_error(monkeypatch):
    import openclaw_runner

    monkeypatch.setattr(openclaw_runner, "openclaw_available", lambda: (True, "openclaw"))
    monkeypatch.setattr(openclaw_runner, "run_process", lambda *a, **k: {
        "ok": False, "error": "exited 1", "stdout": "", "stderr": "Gateway not reachable", "latency_ms": 5})
    out = openclaw_runner.run_openclaw_chat("hello")
    assert out["ok"] is False
    assert "Gateway not reachable" in out["error"]
    assert out.get("stdout") in (None, "")