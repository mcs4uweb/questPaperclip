import pytest

import pricing

MODEL_INFO = {
    "data": [
        {"model_name": "grok-4-6", "model_info": {
            "input_cost_per_token": 2.64e-06, "output_cost_per_token": 7.92e-06,
            "cache_read_input_token_cost": 6.6e-07}},
        {"model_name": "llama3-8b", "model_info": {
            "input_cost_per_token": 3e-07, "output_cost_per_token": 6e-07,
            "cache_read_input_token_cost": None}},
        {"model_name": "no-price", "model_info": {}},
    ]
}


@pytest.fixture(autouse=True)
def fake_proxy(monkeypatch):
    pricing._cache.clear()
    monkeypatch.setattr(pricing, "_fetch_model_info", lambda: MODEL_INFO)


def test_prices_for_known_model():
    p = pricing.prices_for("grok-4-6")
    assert p == {"input": 2.64e-06, "output": 7.92e-06, "cache_read": 6.6e-07, "cache_write": None}


def test_unknown_or_unpriced_model_returns_none():
    assert pricing.prices_for("mystery") is None
    assert pricing.prices_for("no-price") is None


def test_cost_bills_cached_input_at_cache_rate():
    # Real session: 52,147 in (17,361 of them cache reads), 1,587 out.
    usage = {"model": "grok-4-6", "input_tokens": 52147, "output_tokens": 1587,
             "cache_read_tokens": 17361, "cache_write_tokens": 0}
    expected = (52147 - 17361) * 2.64e-06 + 17361 * 6.6e-07 + 1587 * 7.92e-06
    assert pricing.cost_for(usage) == pytest.approx(expected)


def test_cache_reads_fall_back_to_input_rate_when_no_cache_price():
    usage = {"model": "llama3-8b", "input_tokens": 1000, "output_tokens": 100,
             "cache_read_tokens": 400, "cache_write_tokens": 0}
    assert pricing.cost_for(usage) == pytest.approx(1000 * 3e-07 + 100 * 6e-07)


def test_cost_is_none_without_prices():
    assert pricing.cost_for({"model": "mystery", "input_tokens": 10, "output_tokens": 1}) is None


def test_proxy_down_keeps_last_good_prices(monkeypatch):
    assert pricing.prices_for("grok-4-6") is not None
    pricing._cache["fetched_at"] = 0  # force refresh
    monkeypatch.setattr(pricing, "_fetch_model_info", lambda: None)
    assert pricing.prices_for("grok-4-6")["input"] == 2.64e-06


def test_hermes_run_result_carries_cost(monkeypatch):
    import io

    import hermes_runner
    import hermes_usage
    from runner import _from_raw

    class FakeProc:
        pid = 1
        returncode = 0

        def __init__(self, *a, **k):
            self.stdout = io.StringIO("ok\nSession:        s1\n")
            self.stderr = io.StringIO("")

        def poll(self):
            return 0

    monkeypatch.setattr(hermes_runner, "hermes_available", lambda: (True, "hermes"))
    monkeypatch.setattr(hermes_runner.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(hermes_usage, "find_usage", lambda stdout, started_after: {
        "session_id": "s1", "model": "grok-4-6", "input_tokens": 1_000_000,
        "output_tokens": 100_000, "total_tokens": 1_100_000,
        "cache_read_tokens": 0, "cache_write_tokens": 0, "api_calls": 1})

    result = _from_raw(hermes_runner.run_hermes_chat("hi"), model="grok-4-6")
    assert result.cost == pytest.approx(2.64 + 0.792)
