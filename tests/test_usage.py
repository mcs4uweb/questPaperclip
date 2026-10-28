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
