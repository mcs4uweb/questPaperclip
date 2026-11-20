import io
from usage import parse_usage


SAMPLE_HERMES_FOOTER = """
╭────────────────────────────╮
│ grok-4-6 grok-ok           │
╰────────────────────────────╯

Session: sess-abc
Tokens: 1,250 (800 in / 450 out)
Cost: $0.0042
"""


def test_hermes_footer_parses_tokens_and_cost():
    parsed = parse_usage(SAMPLE_HERMES_FOOTER)
    assert parsed.source == "parsed"
    assert parsed.tokens == 1250
    assert parsed.cost == 0.0042


def test_footerless_stdout_is_unknown_not_word_count():
    text = "The agent finished the task and wrote three files."
    parsed = parse_usage(text)
    assert parsed.source == "unknown"
    assert parsed.tokens is None
    assert parsed.cost is None
    assert parsed.tokens != len(text.split())


def test_provider_usage_dict_is_parsed():
    parsed = parse_usage(
        "ok",
        provider_usage={
            "prompt_tokens": 100,
            "completion_tokens": 40,
            "total_tokens": 140,
            "cost": 0.01,
        },
    )
    assert parsed.source == "parsed"
    assert parsed.tokens == 140
    assert parsed.cost == 0.01


def test_usage_json_embedded_in_stdout():
    parsed = parse_usage('result ok\n{"usage": {"total_tokens": 77, "cost": 0.003}}')
    assert parsed.source == "parsed"
    assert parsed.tokens == 77
    assert parsed.cost == 0.003


def test_hermes_runner_does_not_invent_word_counts(monkeypatch):
    from hermes_runner import run_hermes_chat

    monkeypatch.setattr("hermes_runner.hermes_available", lambda: (True, "hermes"))

    class FakeProc:
        pid = 99
        returncode = 0

        def __init__(self):
            self.stdout = io.StringIO("The agent finished the task and wrote three files.")
            self.stderr = io.StringIO("")

        def poll(self):
            return 0

        def communicate(self, timeout=None):
            return ("The agent finished the task and wrote three files.", "")

        def terminate(self):
            return None

        def kill(self):
            return None

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr("hermes_runner.subprocess.Popen", lambda *args, **kwargs: FakeProc())
    out = run_hermes_chat("one two three four five six")
    words = len("one two three four five six".split()) + len("The agent finished the task and wrote three files.".split())
    assert out.get("token_count") in (None, 0)
    assert out.get("tokens") in (None, 0)
    assert out.get("token_count") != words


def test_openclaw_persists_provider_usage(monkeypatch):
    import json

    import openclaw_runner
    from runner import _from_raw

    agent_json = {
        "status": "ok", "summary": "completed",
        "result": {
            "payloads": [{"text": "PONG"}],
            "meta": {"agentMeta": {
                "sessionId": "paperclip-job-1", "model": "grok-4-6",
                "usage": {"input": 24653, "output": 3, "total": 24656, "cost": {"total": 0.019732}},
            }},
        },
    }
    seen = {}

    def fake_run_process(args, **kwargs):
        seen["args"] = args
        msg_file = args[args.index("--message-file") + 1]
        seen["message"] = open(msg_file, encoding="utf-8").read()
        return {"ok": True, "error": None, "stdout": json.dumps(agent_json), "stderr": "", "latency_ms": 9}

    monkeypatch.setattr(openclaw_runner, "openclaw_available", lambda: (True, "openclaw"))
    monkeypatch.setattr(openclaw_runner, "run_process", fake_run_process)
    raw = openclaw_runner.run_openclaw_chat("hello & <world> 100%", job_id="job-1")

    assert seen["message"] == "hello & <world> 100%"  # passed via file, not argv
    assert seen["args"][seen["args"].index("--session-id") + 1] == "paperclip-job-1"
    result = _from_raw(raw, model="openclaw")
    assert result.ok and result.stdout == "PONG"
    assert (result.input_tokens, result.output_tokens, result.tokens) == (24653, 3, 24656)
    assert result.cost == 0.019732 and result.usage_source == "parsed"