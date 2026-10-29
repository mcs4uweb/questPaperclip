"""Async job queue: one running job per agent, cancel + force-idle."""

from __future__ import annotations

import threading
import time
from typing import Optional
from uuid import uuid4

import db
from runner import Result, is_runnable_kind, run_agent

JOB_STATUSES = ("queued", "running", "succeeded", "failed", "cancelled")
OPEN_STATUSES = ("queued", "running")

_cancel_requested: set[str] = set()
_job_pids: dict[str, int] = {}
_lock = threading.Lock()
_worker_started = False


def start_worker() -> None:
    global _worker_started
    with _lock:
        if _worker_started:
            return
        _worker_started = True
    thread = threading.Thread(target=_loop, name="paperclip-jobs", daemon=True)
    thread.start()


def _loop() -> None:
    while True:
        try:
            _tick()
        except Exception:
            pass
        time.sleep(0.05)


def _tick() -> None:
    db.reset_all_daily_spend_if_needed()
    job = db.claim_next_job()
    if not job:
        return
    _execute(job)


def is_cancel_requested(job_id: str) -> bool:
    with _lock:
        return job_id in _cancel_requested


def request_cancel(job_id: str) -> None:
    with _lock:
        _cancel_requested.add(job_id)
        pid = _job_pids.get(job_id)
    if pid:
        _kill_pid(pid)


def remember_pid(job_id: str, pid: int) -> None:
    with _lock:
        _job_pids[job_id] = pid


def forget_job(job_id: str) -> None:
    with _lock:
        _cancel_requested.discard(job_id)
        _job_pids.pop(job_id, None)


def _kill_pid(pid: int) -> None:
    try:
        import os
        import signal

        os.kill(pid, signal.SIGTERM)
    except OSError:
        try:
            import subprocess

            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)
        except OSError:
            pass


def enqueue(
    agent: dict,
    *,
    goal: str,
    cwd: str = "",
    kind: Optional[str] = None,
    ticket_id: Optional[str] = None,
) -> dict:
    db.reset_daily_spend_if_needed(agent["id"])
    agent = db.get_agent(agent["id"]) or agent
    resolved_kind = (kind or agent.get("kind") or "").strip().lower()
    if not is_runnable_kind(resolved_kind):
        raise ValueError(
            f"Agent kind {resolved_kind or 'unknown'!r} is display-only and is not routed through a CLI"
        )
    if not goal.strip():
        raise ValueError("empty goal")
    if agent.get("status") == "paused":
        raise PermissionError("Agent is paused")
    cap = float(agent.get("daily_cap") or 0)
    spend = float(agent.get("daily_spend") or 0)
    if cap > 0 and spend >= cap:
        db.update_agent(agent["id"], status="exceeded")
        raise PermissionError("Daily budget cap reached")

    return db.create_job(
        job_id=f"job-{uuid4().hex[:10]}",
        agent_id=agent["id"],
        ticket_id=ticket_id,
        kind=resolved_kind,
        goal=goal.strip(),
        cwd=cwd or "",
    )


def cancel_job(job_id: str) -> Optional[dict]:
    job = db.get_job(job_id)
    if not job:
        return None
    if job["status"] == "queued":
        updated = db.update_job(job_id, status="cancelled", finished_at=db.now_iso(), error="cancelled")
        _write_cancelled_trace(updated)
        _maybe_idle_agent(job["agent_id"])
        return updated
    if job["status"] == "running":
        request_cancel(job_id)
        return db.get_job(job_id)
    return job


def force_idle(agent_id: str) -> Optional[dict]:
    agent = db.get_agent(agent_id)
    if not agent:
        return None
    for job in db.list_open_jobs(agent_id):
        cancel_job(job["id"])
        if job["status"] == "running":
            request_cancel(job["id"])
            db.update_job(job["id"], status="cancelled", finished_at=db.now_iso(), error="cancelled")
            _write_cancelled_trace(db.get_job(job["id"]))
    forget_open = db.list_jobs(agent_id=agent_id)
    for job in forget_open:
        if job["status"] in OPEN_STATUSES:
            db.update_job(job["id"], status="cancelled", finished_at=db.now_iso(), error="cancelled")
            _write_cancelled_trace(db.get_job(job["id"]))
        forget_job(job["id"])
    return db.update_agent(agent_id, status="idle")


def _maybe_idle_agent(agent_id: str) -> None:
    if db.get_running_job(agent_id):
        return
    agent = db.get_agent(agent_id)
    if agent and agent.get("status") == "running":
        db.update_agent(agent_id, status="idle")


def _write_cancelled_trace(job: Optional[dict]) -> None:
    if not job:
        return
    agent = db.get_agent(job["agent_id"])
    db.add_trace(
        trace_id=f"tr-{uuid4().hex[:6]}",
        agent_id=job["agent_id"],
        agent_name=(agent or {}).get("name") or job["agent_id"],
        tool_called=job.get("kind") or "run",
        prompt=job.get("goal") or "",
        response="cancelled",
        latency_ms=int(job.get("latency_ms") or 0),
        token_count=int(job.get("tokens") or 0),
        status="Cancelled",
    )


def _execute(job: dict) -> None:
    job_id = job["id"]
    agent = db.get_agent(job["agent_id"])
    if not agent:
        db.update_job(job_id, status="failed", error="Agent not found", finished_at=db.now_iso())
        return
    if is_cancel_requested(job_id):
        db.update_job(job_id, status="cancelled", error="cancelled", finished_at=db.now_iso())
        _write_cancelled_trace(db.get_job(job_id))
        forget_job(job_id)
        _maybe_idle_agent(agent["id"])
        return

    db.reset_daily_spend_if_needed(agent["id"])
    agent = db.get_agent(agent["id"]) or agent
    db.update_agent(agent["id"], status="running", last_heartbeat=db.now_iso())
    started = db.now_iso()
    db.update_job(job_id, status="running", started_at=started)

    def pid_callback(pid: int) -> None:
        remember_pid(job_id, pid)

    result: Result = run_agent(
        agent,
        job["goal"],
        cwd=job.get("cwd") or None,
        job_id=job_id,
        cancel_check=lambda: is_cancel_requested(job_id),
        pid_callback=pid_callback,
    )

    if is_cancel_requested(job_id):
        db.update_job(
            job_id,
            status="cancelled",
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            error="cancelled",
            tokens=result.tokens,
            cost=result.cost,
            latency_ms=result.latency_ms,
            usage_source=result.usage_source,
            finished_at=db.now_iso(),
        )
        _write_cancelled_trace(db.get_job(job_id))
        forget_job(job_id)
        _maybe_idle_agent(agent["id"])
        return

    _finish(agent, job, result)


def _finish(agent: dict, job: dict, result: Result) -> None:
    job_id = job["id"]
    tokens = result.tokens
    cost = result.cost if result.cost is not None else 0.0
    if result.usage_source != "parsed":
        tokens = None
        cost = 0.0

    next_spend = round(float(agent.get("daily_spend") or 0) + float(cost or 0), 4)
    monthly_spend = round(float(agent.get("monthly_spend") or 0) + float(cost or 0), 4)
    added_tokens = int(tokens or 0)
    status = "idle"
    if agent.get("daily_cap") and next_spend >= float(agent["daily_cap"]) and float(agent["daily_cap"]) > 0:
        status = "exceeded"
    elif not result.ok:
        status = "paused"

    db.update_job(
        job_id,
        status="succeeded" if result.ok else "failed",
        stdout=result.stdout or "",
        stderr=result.stderr or "",
        error=None if result.ok else (result.error or "failed"),
        tokens=tokens,
        cost=cost if result.usage_source == "parsed" else None,
        latency_ms=result.latency_ms,
        usage_source=result.usage_source,
        finished_at=db.now_iso(),
    )
    db.update_agent(
        agent["id"],
        status=status,
        daily_spend=next_spend,
        monthly_spend=monthly_spend,
        last_heartbeat=db.now_iso(),
        total_tokens=int(agent.get("total_tokens") or 0) + added_tokens,
        last_run_summary=(result.stdout or result.error or "")[:2000],
        goal=job.get("goal") or agent.get("goal") or "",
        working_dir=job.get("cwd") or agent.get("working_dir") or "",
        usage_source=result.usage_source,
        spend_date=db.chicago_today(),
    )
    db.add_trace(
        trace_id=f"tr-{uuid4().hex[:6]}",
        agent_id=agent["id"],
        agent_name=agent.get("name") or agent["id"],
        tool_called=job.get("kind") or "run",
        prompt=job.get("goal") or "",
        response=(result.stdout or result.error or "")[:4000],
        token_count=added_tokens,
        latency_ms=int(result.latency_ms or 0),
        status="Success" if result.ok else "Error",
    )
    forget_job(job_id)
