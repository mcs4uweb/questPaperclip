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
