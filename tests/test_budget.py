from tests.conftest import make_agent, wait_job


def test_heartbeat_does_not_invent_spend(client):
    agent = make_agent(client)
    before = client.get(f"/api/agents/{agent['id']}").json()
    res = client.post(
        f"/api/agents/{agent['id']}/heartbeat",
        json={"note": "dashboard ping"},
    )
    assert res.status_code == 200
    after = client.get(f"/api/agents/{agent['id']}").json()
    assert after["daily_spend"] == before["daily_spend"]
    assert after["total_tokens"] == before["total_tokens"]


def test_classic_dashboard_heartbeat_payload_is_ping_only():
    from pathlib import Path

    html = Path(__file__).resolve().parents[1].joinpath("static", "index.html").read_text(encoding="utf-8")
    assert "tokens_consumed: 250" not in html
    assert "cost_incurred: 0.04" not in html
    assert "ping_only: true" in html


def test_budget_halt_when_spend_at_cap(client):
    import db

    agent = make_agent(client, daily_cap=1.0, goal="should halt")
    db.update_agent(agent["id"], daily_spend=1.0, spend_date=db.chicago_today())
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "should halt"})
    assert res.status_code == 403


def test_daily_spend_resets_at_chicago_midnight(client):
    import db

    agent = make_agent(client)
    db.update_agent(
        agent["id"],
        daily_spend=4.5,
        total_tokens=900,
        spend_date="1999-01-01",
    )
    db.reset_daily_spend_if_needed(agent["id"])
    after = db.get_agent(agent["id"])
    assert after["daily_spend"] == 0
    assert after["total_tokens"] == 900


def test_run_with_unknown_usage_does_not_count_words(client):
    agent = make_agent(client, goal="NOUSAGE please")
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "NOUSAGE please"})
    job = wait_job(client, res.json()["job_id"])
    assert job["status"] == "succeeded"
    assert job.get("usage_source") == "unknown"
    assert job["tokens"] in (None, 0)
    after = client.get(f"/api/agents/{agent['id']}").json()
    assert after["daily_spend"] == 0
    assert after.get("usage_source") == "unknown"


def test_parsed_usage_updates_daily_and_monthly_spend(client):
    agent = make_agent(client, goal="say hello")
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "say hello"})
    job = wait_job(client, res.json()["job_id"])
    assert job["status"] == "succeeded"
    assert job.get("usage_source") == "parsed"
    assert job["tokens"] == 12
    assert job["cost"] == 0.02
    after = client.get(f"/api/agents/{agent['id']}").json()
    assert after["daily_spend"] == 0.02
    assert after["monthly_spend"] == 0.02
    assert after["total_tokens"] == 12
    assert after["usage_source"] == "parsed"


def test_company_monthly_cap_is_stored_not_daily_times_12_4(client):
    first = client.get("/api/company").json()
    assert "monthly_cap" in first
    assert first["monthly_cap"] > 0
    res = client.patch("/api/company", json={"monthly_cap": 200})
    assert res.status_code == 200
    assert res.json()["monthly_cap"] == 200
    again = client.get("/api/company").json()
    assert again["monthly_cap"] == 200
    assert again["monthly_spend"] == first["monthly_spend"]
