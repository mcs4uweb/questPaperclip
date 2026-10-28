from tests.conftest import make_agent, wait_job


def test_health_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["storage"] == "sqlite"


def test_run_without_goal_is_400_and_creates_no_job(client):
    agent = make_agent(client, goal="")
    before = client.get("/api/jobs").json()
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "  "})
    assert res.status_code == 400
    after = client.get("/api/jobs").json()
    assert len(after) == len(before)


def test_run_returns_202_and_job_completes(client):
    agent = make_agent(client, goal="say hello")
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "say hello"})
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "queued"
    assert body["job_id"]
    job = wait_job(client, body["job_id"])
    assert job["status"] == "succeeded"
    assert job["stdout"] == "hello from fake"
    assert job["tokens"] == 12
    assert job["cost"] == 0.02

    live = client.get(f"/api/jobs/{body['job_id']}")
    assert live.status_code == 200
    agent_after = client.get(f"/api/agents/{agent['id']}")
    assert agent_after.status_code == 200
    assert agent_after.json()["status"] != "running"


def test_kind_specific_run_is_alias(client):
    agent = make_agent(client, kind="hermes", goal="alias")
    res = client.post(f"/api/agents/{agent['id']}/hermes/run", json={"goal": "alias"})
    assert res.status_code == 202
    job = wait_job(client, res.json()["job_id"])
    assert job["status"] == "succeeded"
    assert job["kind"] == "hermes"


def test_second_run_queues_behind_running_job(client):
    agent = make_agent(client, goal="SLEEP first")
    first = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "SLEEP first"})
    assert first.status_code == 202
    second = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "after"})
    assert second.status_code == 202
    job2 = client.get(f"/api/jobs/{second.json()['job_id']}").json()
    assert job2["status"] in {"queued", "running", "succeeded"}
    wait_job(client, first.json()["job_id"], timeout=8)
    done = wait_job(client, second.json()["job_id"], timeout=8)
    assert done["status"] == "succeeded"


def test_paused_agent_does_not_enqueue(client):
    agent = make_agent(client, status="paused", goal="nope")
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "nope"})
    assert res.status_code == 403
    assert client.get("/api/jobs").json() == []


def test_over_cap_agent_does_not_enqueue(client):
    import db

    agent = make_agent(client, daily_cap=1.0, goal="nope")
    db.update_agent(agent["id"], daily_spend=1.0, spend_date=db.chicago_today())
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "nope"})
    assert res.status_code == 403
    assert client.get("/api/jobs").json() == []


def test_display_only_kind_is_not_routed(client):
    agent = make_agent(client, kind="display", name="Quest Display", goal="should not run")
    res = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "should not run"})
    assert res.status_code == 400
    assert "display" in res.json()["detail"].lower() or "kind" in res.json()["detail"].lower()
