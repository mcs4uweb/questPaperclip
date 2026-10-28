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


def test_openclaw_unknown_json_is_readable_error(monkeypatch):
    from openclaw_runner import run_openclaw_chat

    def fake_post(url, body, timeout_sec):
        return 200, {"weird": True, "nested": {"x": 1}}, '{"weird": true}'

    monkeypatch.setattr("openclaw_runner._post", fake_post)
    out = run_openclaw_chat("hello")
    assert out["ok"] is False
    assert "HTTP" in out["error"] or "unrecognized" in out["error"].lower()
    assert out.get("stdout") in (None, "")
