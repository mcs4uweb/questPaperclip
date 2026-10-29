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
    from openclaw_runner import run_openclaw_chat

    payload = {
        "output": "ok",
        "usage": {"total_tokens": 88, "cost": 0.015},
    }

    def fake_post(url, body, timeout_sec):
        assert body == {"message": "hello"}
        return 200, payload, '{"output":"ok"}'

    monkeypatch.setattr("openclaw_runner._post", fake_post)
    out = run_openclaw_chat("hello")
    assert out["ok"] is True
    assert out.get("usage") == {"total_tokens": 88, "cost": 0.015}
    assert out.get("token_count") in (None, 0)
