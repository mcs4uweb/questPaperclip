from tests.conftest import make_agent, wait_job


def test_cancel_queued_job_sets_cancelled_and_idle(client):
    agent = make_agent(client, goal="SLEEP first")
    first = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "SLEEP first"})
    second = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "queued later"})
    assert first.status_code == 202
    assert second.status_code == 202

    cancel = client.post(f"/api/jobs/{second.json()['job_id']}/cancel")
    assert cancel.status_code == 200
    job = client.get(f"/api/jobs/{second.json()['job_id']}").json()
    assert job["status"] == "cancelled"

    wait_job(client, first.json()["job_id"], timeout=8)
    agent_after = client.get(f"/api/agents/{agent['id']}").json()
    assert agent_after["status"] in {"idle", "paused", "exceeded"}


def test_force_idle_cancels_open_jobs(client):
    agent = make_agent(client, goal="SLEEP now")
    queued = client.post(f"/api/agents/{agent['id']}/run", json={"goal": "SLEEP now"})
    assert queued.status_code == 202
    idle = client.post(f"/api/agents/{agent['id']}/idle")
    assert idle.status_code == 200
    assert idle.json()["status"] == "idle"
    job = wait_job(client, queued.json()["job_id"], timeout=8)
    assert job["status"] == "cancelled"
    traces = client.get("/api/traces?limit=20").json()
    cancelled = [t for t in traces if t["status"] == "Cancelled"]
    assert cancelled, traces
