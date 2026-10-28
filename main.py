from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import db

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Quest Paperclip",
    version="1.1.0",
    description="Local agent control plane: org, tickets, budgets, heartbeats, and traces (SQLite).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Agent(BaseModel):
    id: str
    name: str
    role: str
    provider: str
    model: str
    status: Literal["idle", "running", "paused", "exceeded"] = "idle"
    daily_spend: float = 0.0
    daily_cap: float = 10.0
    last_heartbeat: Optional[datetime] = None
    reports_to: Optional[str] = None
    kind: str = "openclaw"
    goal: str = ""
    working_dir: str = ""
    total_tokens: int = 0
    last_run_summary: str = ""
    avatar_color: str = "bg-indigo-500"


TICKET_STATUSES = Literal["todo", "in-progress", "done", "backlog", "assigned", "review", "completed"]
STORY_PRIORITIES = Literal["P0", "P1", "P2", "P3", "Low", "Medium", "High", "Critical"]


class Ticket(BaseModel):
    id: str
    title: str
    description: str = ""
    assignee_id: str
    priority: str = "P2"
    status: str = "todo"
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    story_id: Optional[str] = None
    epic: str = ""
    sprint: str = ""
    as_a: str = ""
    i_want: str = ""
    so_that: str = ""
    blocked_by: str = ""
    must_not: str = ""
    files_existing: str = ""
    files_create: str = ""
    acceptance: str = ""
    test_plan: str = ""
    pr_size: str = "one concern"
    tags: str = "user-story"


class TraceLog(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    tool_called: str
    prompt: str
    response: str
    latency_ms: int = 0
    token_count: int = 0
    status: str = "Success"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HeartbeatIn(BaseModel):
    tokens_consumed: int = 0
    cost_incurred: float = 0.0
    current_task_id: Optional[str] = None
    note: str = ""


class TicketCreate(BaseModel):
    title: str
    description: str = ""
    assignee_id: str
    priority: STORY_PRIORITIES = "P2"
    status: TICKET_STATUSES = "todo"
    story_id: Optional[str] = None
    epic: str = ""
    sprint: str = ""
    as_a: str = ""
    i_want: str = ""
    so_that: str = ""
    blocked_by: str = ""
    must_not: str = ""
    files_existing: str = ""
    files_create: str = ""
    acceptance: str = ""
    test_plan: str = ""
    pr_size: str = "one concern"
    tags: str = "user-story"


class TicketStatusIn(BaseModel):
    status: TICKET_STATUSES


class AgentStatusIn(BaseModel):
    status: Literal["idle", "running", "paused", "exceeded"]


class BudgetIn(BaseModel):
    daily_cap: float


class AgentGoalIn(BaseModel):
    goal: str = ""
    working_dir: Optional[str] = None


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=1, max_length=200)
    provider: str = "openclaw"
    model: str = "openclaw"
    daily_cap: float = 5.0
    reports_to: Optional[str] = None
    status: Literal["idle", "running", "paused", "exceeded"] = "idle"
    kind: str = "hermes"
    goal: str = ""
    working_dir: str = ""


class HermesRunIn(BaseModel):
    goal: Optional[str] = None
    working_dir: Optional[str] = None
    timeout_sec: Optional[int] = Field(default=None, ge=1, le=86400)


class OpenClawRunIn(BaseModel):
    goal: Optional[str] = None
    timeout_sec: int = Field(default=90, ge=5, le=300)
    url: Optional[str] = None


class NanoclawRunIn(BaseModel):
    goal: Optional[str] = None
    working_dir: Optional[str] = None
    timeout_sec: Optional[int] = Field(default=None, ge=1, le=86400)


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def agent_from_row(row: dict) -> Agent:
    return Agent(
        id=row["id"],
        name=row["name"],
        role=row["role"],
        provider=row["provider"],
        model=row["model"],
        status=row["status"],
        daily_spend=row["daily_spend"],
        daily_cap=row["daily_cap"],
        last_heartbeat=parse_dt(row.get("last_heartbeat")),
        reports_to=row.get("reports_to"),
        kind=row.get("kind") or "hermes",
        goal=row.get("goal") or "",
        working_dir=row.get("working_dir") or "",
        total_tokens=row.get("total_tokens") or 0,
        last_run_summary=row.get("last_run_summary") or "",
        avatar_color=row.get("avatar_color") or "bg-indigo-500",
    )


def ticket_from_row(row: dict) -> Ticket:
    return Ticket(
        id=row["id"],
        title=row["title"],
        description=row.get("description") or "",
        assignee_id=row["assignee_id"],
        priority=row["priority"],
        status=row["status"],
        tokens_used=row["tokens_used"],
        created_at=parse_dt(row["created_at"]) or datetime.now(timezone.utc),
        story_id=row.get("story_id"),
        epic=row.get("epic") or "",
        sprint=row.get("sprint") or "",
        as_a=row.get("as_a") or "",
        i_want=row.get("i_want") or "",
        so_that=row.get("so_that") or "",
        blocked_by=row.get("blocked_by") or "",
        must_not=row.get("must_not") or "",
        files_existing=row.get("files_existing") or "",
        files_create=row.get("files_create") or "",
        acceptance=row.get("acceptance") or "",
        test_plan=row.get("test_plan") or "",
        pr_size=row.get("pr_size") or "one concern",
        tags=row.get("tags") or "user-story",
    )


def trace_from_row(row: dict) -> TraceLog:
    return TraceLog(
        id=row["id"],
        agent_id=row["agent_id"],
        agent_name=row["agent_name"],
        tool_called=row["tool_called"],
        prompt=row["prompt"],
        response=row["response"],
        latency_ms=row["latency_ms"],
        token_count=row["token_count"],
        status=row["status"],
        timestamp=parse_dt(row["timestamp"]) or datetime.now(timezone.utc),
    )


def record_trace(**kwargs) -> TraceLog:
    row = db.add_trace(trace_id=f"tr-{uuid4().hex[:6]}", **kwargs)
    return trace_from_row(row)


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/health")
def health():
    agents = db.list_agents()
    tickets = db.list_tickets()
    return {
        "status": "ok",
        "app": "Quest Paperclip",
        "company": "Quest Studio",
        "storage": "sqlite",
        "db_path": str(db.DB_PATH),
        "agents": len(agents),
        "tickets": len(tickets),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/company")
def company():
    agents = db.list_agents()
    tickets = db.list_tickets()
    spend = round(sum(a["daily_spend"] for a in agents), 4)
    cap = round(sum(a["daily_cap"] for a in agents), 2)
    return {
        "name": "Quest Studio",
        "goal": "Ship math-learning videos and keep investing / home-energy work organized without extra Telegram noise.",
        "daily_spend": spend,
        "daily_cap": cap,
        "active_agents": sum(1 for a in agents if a["status"] == "running"),
        "open_tickets": sum(1 for t in tickets if t["status"] not in ("completed", "done")),
    }


@app.get("/api/agents", response_model=List[Agent])
def list_agents():
    return [agent_from_row(row) for row in db.list_agents()]


@app.post("/api/agents", response_model=Agent)
def create_agent(body: AgentCreate):
    if body.reports_to and not db.get_agent(body.reports_to):
        raise HTTPException(400, "Unknown reports_to agent")
    row = db.create_agent(
        name=body.name,
        role=body.role,
        provider=body.provider,
        model=body.model,
        daily_cap=max(0.0, body.daily_cap),
        reports_to=body.reports_to,
        status=body.status,
        kind=body.kind,
        goal=body.goal,
        working_dir=body.working_dir,
    )
    return agent_from_row(row)


@app.patch("/api/agents/{agent_id}/status", response_model=Agent)
def set_agent_status(agent_id: str, body: AgentStatusIn):
    if not db.get_agent(agent_id):
        raise HTTPException(404, "Agent not found")
    row = db.update_agent(agent_id, status=body.status)
    return agent_from_row(row)


@app.patch("/api/agents/{agent_id}/goal", response_model=Agent)
def set_agent_goal(agent_id: str, body: AgentGoalIn):
    if not db.get_agent(agent_id):
        raise HTTPException(404, "Agent not found")
    fields = {"goal": body.goal}
    if body.working_dir is not None:
        fields["working_dir"] = body.working_dir
    row = db.update_agent(agent_id, **fields)
    return agent_from_row(row)


@app.patch("/api/agents/{agent_id}/budget", response_model=Agent)
def set_agent_budget(agent_id: str, body: BudgetIn):
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    daily_cap = max(0.0, body.daily_cap)
    status = agent["status"]
    if agent["daily_spend"] >= daily_cap and daily_cap > 0:
        status = "exceeded"
    row = db.update_agent(agent_id, daily_cap=daily_cap, status=status)
    return agent_from_row(row)


@app.post("/api/agents/{agent_id}/heartbeat")
def heartbeat(agent_id: str, body: HeartbeatIn):
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent["status"] == "paused":
        raise HTTPException(403, "Agent is paused")

    next_spend = round(agent["daily_spend"] + body.cost_incurred, 4)
    if next_spend > agent["daily_cap"]:
        db.update_agent(agent_id, status="exceeded")
        record_trace(
            agent_id=agent["id"],
            agent_name=agent["name"],
            tool_called="heartbeat",
            prompt=body.note or "heartbeat",
            response=f"HALT: cap ${agent['daily_cap']:.2f}",
            token_count=body.tokens_consumed,
            status="Blocked by Cap",
        )
        raise HTTPException(
            403,
            f"Daily budget cap ${agent['daily_cap']:.2f} reached. Agent paused.",
        )

    db.update_agent(
        agent_id,
        daily_spend=next_spend,
        last_heartbeat=db.now_iso(),
        status="running",
    )

    if body.current_task_id:
        ticket = db.get_ticket(body.current_task_id)
        if ticket:
            fields = {"tokens_used": ticket["tokens_used"] + body.tokens_consumed}
            if ticket["status"] in ("backlog", "assigned"):
                fields["status"] = "in_progress"
            db.update_ticket(body.current_task_id, **fields)

    remaining = round(agent["daily_cap"] - next_spend, 4)
    record_trace(
        agent_id=agent["id"],
        agent_name=agent["name"],
        tool_called="heartbeat",
        prompt=body.note or f"task={body.current_task_id or 'none'}",
        response=f"CONTINUE remaining=${remaining:.2f}",
        token_count=body.tokens_consumed,
        latency_ms=42,
        status="Success",
    )
    return {
        "action": "CONTINUE",
        "agent_id": agent["id"],
        "current_spend": next_spend,
        "remaining_budget": remaining,
        "state": "running",
    }


@app.get("/api/tickets", response_model=List[Ticket])
def list_tickets():
    return [ticket_from_row(row) for row in db.list_tickets()]


@app.post("/api/tickets", response_model=Ticket)
def create_ticket(body: TicketCreate):
    if not db.get_agent(body.assignee_id):
        raise HTTPException(400, "Unknown assignee")
    row = db.create_ticket(
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
        priority=body.priority,
        status=body.status,
        story_id=body.story_id,
        epic=body.epic,
        sprint=body.sprint,
        as_a=body.as_a,
        i_want=body.i_want,
        so_that=body.so_that,
        blocked_by=body.blocked_by,
        must_not=body.must_not,
        files_existing=body.files_existing,
        files_create=body.files_create,
        acceptance=body.acceptance,
        test_plan=body.test_plan,
        pr_size=body.pr_size,
        tags=body.tags,
    )
    return ticket_from_row(row)


@app.put("/api/tickets/{ticket_id}/status", response_model=Ticket)
def update_ticket_status(ticket_id: str, body: TicketStatusIn):
    if not db.get_ticket(ticket_id):
        raise HTTPException(404, "Ticket not found")
    row = db.update_ticket(ticket_id, status=body.status)
    return ticket_from_row(row)


@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: str):
    if not db.delete_ticket(ticket_id):
        raise HTTPException(404, "Ticket not found")
    return {"deleted": ticket_id}


@app.get("/api/traces", response_model=List[TraceLog])
def list_traces(limit: int = 50):
    return [trace_from_row(row) for row in db.list_traces(max(1, min(limit, 200)))]


@app.get("/api/hermes/status")
def hermes_status():
    from hermes_runner import hermes_available

    found, path = hermes_available()
    return {"available": found, "path": path}


@app.get("/api/nanoclaw/status")
def nanoclaw_status():
    from nanoclaw_runner import nanoclaw_available

    found, path = nanoclaw_available()
    return {"available": found, "path": path}


@app.post("/api/agents/{agent_id}/nanoclaw/run")
def run_nanoclaw_agent(agent_id: str, body: NanoclawRunIn):
    from nanoclaw_runner import run_nanoclaw_chat

    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent.get("status") == "paused":
        raise HTTPException(403, "Agent is paused")
    if agent["daily_spend"] >= agent["daily_cap"] and agent["daily_cap"] > 0:
        db.update_agent(agent_id, status="exceeded")
        raise HTTPException(403, "Daily budget cap reached")

    goal = (body.goal or agent.get("goal") or "").strip()
    if not goal:
        raise HTTPException(400, "Nanoclaw agent needs a goal")
    working_dir = (body.working_dir or agent.get("working_dir") or "").strip() or None

    db.update_agent(agent_id, status="running", last_heartbeat=db.now_iso())
    result = run_nanoclaw_chat(goal, cwd=working_dir, timeout_sec=body.timeout_sec)

    tokens = int(result.get("token_count") or 0)
    cost = round(tokens * 0.000002, 6)
    next_spend = round(float(agent["daily_spend"]) + cost, 4)
    status = "exceeded" if next_spend >= agent["daily_cap"] and agent["daily_cap"] > 0 else "idle"
    if not result.get("ok"):
        status = "paused"

    db.update_agent(
        agent_id,
        status=status,
        daily_spend=next_spend,
        last_heartbeat=db.now_iso(),
        total_tokens=int(agent.get("total_tokens") or 0) + tokens,
        last_run_summary=(result.get("stdout") or result.get("error") or "")[:2000],
        goal=goal,
        working_dir=working_dir or "",
        kind="nanoclaw",
        provider="nanoclaw",
        model="nanoclaw",
    )
    record_trace(
        agent_id=agent["id"],
        agent_name=agent["name"],
        tool_called="nanoclaw",
        prompt=goal,
        response=(result.get("stdout") or result.get("error") or "")[:4000],
        token_count=tokens,
        latency_ms=int(result.get("latency_ms") or 0),
        status="Success" if result.get("ok") else "Error",
    )
    return {
        "ok": result.get("ok"),
        "agent_id": agent_id,
        "action": "CONTINUE" if result.get("ok") else "HALT",
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
        "error": result.get("error"),
        "latency_ms": result.get("latency_ms"),
        "token_count": tokens,
        "state": status,
        "argv": result.get("argv"),
    }


@app.post("/api/agents/{agent_id}/hermes/run")
def run_hermes_agent(agent_id: str, body: HermesRunIn):
    from hermes_runner import run_hermes_chat

    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent.get("status") == "paused":
        raise HTTPException(403, "Agent is paused")
    if agent["daily_spend"] >= agent["daily_cap"] and agent["daily_cap"] > 0:
        db.update_agent(agent_id, status="exceeded")
        raise HTTPException(403, "Daily budget cap reached")

    goal = (body.goal or agent.get("goal") or "").strip()
    if not goal:
        raise HTTPException(400, "Hermes agent needs a goal")
    working_dir = (body.working_dir or agent.get("working_dir") or "").strip() or None

    db.update_agent(agent_id, status="running", last_heartbeat=db.now_iso())
    result = run_hermes_chat(goal, cwd=working_dir, timeout_sec=body.timeout_sec)

    tokens = int(result.get("token_count") or 0)
    cost = round(tokens * 0.000002, 6)
    next_spend = round(float(agent["daily_spend"]) + cost, 4)
    status = "exceeded" if next_spend >= agent["daily_cap"] and agent["daily_cap"] > 0 else "idle"
    if not result.get("ok"):
        status = "paused" if agent.get("kind") == "hermes" else "idle"

    db.update_agent(
        agent_id,
        status=status,
        daily_spend=next_spend,
        last_heartbeat=db.now_iso(),
        total_tokens=int(agent.get("total_tokens") or 0) + tokens,
        last_run_summary=(result.get("stdout") or result.get("error") or "")[:2000],
        goal=goal,
        working_dir=working_dir or "",
    )
    record_trace(
        agent_id=agent["id"],
        agent_name=agent["name"],
        tool_called="hermes_chat",
        prompt=goal,
        response=(result.get("stdout") or result.get("error") or "")[:4000],
        token_count=tokens,
        latency_ms=int(result.get("latency_ms") or 0),
        status="Success" if result.get("ok") else "Error",
    )
    return {
        "ok": result.get("ok"),
        "agent_id": agent_id,
        "action": "CONTINUE" if result.get("ok") else "HALT",
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
        "error": result.get("error"),
        "latency_ms": result.get("latency_ms"),
        "token_count": tokens,
        "state": status,
    }


@app.get("/api/openclaw/status")
def openclaw_status():
    from openclaw_runner import openclaw_status as probe

    return probe()


@app.post("/api/openclaw/chat")
def openclaw_chat(body: OpenClawRunIn):
    from openclaw_runner import run_openclaw_chat

    goal = (body.goal or "").strip()
    if not goal:
        raise HTTPException(400, "OpenClaw needs a goal")
    return run_openclaw_chat(goal, url=body.url or None, timeout_sec=body.timeout_sec)


@app.post("/api/agents/{agent_id}/openclaw/run")
def run_openclaw_agent(agent_id: str, body: OpenClawRunIn):
    from openclaw_runner import DEFAULT_URL, run_openclaw_chat

    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent.get("status") == "paused":
        raise HTTPException(403, "Agent is paused")
    if agent["daily_spend"] >= agent["daily_cap"] and agent["daily_cap"] > 0:
        db.update_agent(agent_id, status="exceeded")
        raise HTTPException(403, "Daily budget cap reached")

    goal = (body.goal or agent.get("goal") or "").strip()
    if not goal:
        raise HTTPException(400, "OpenClaw agent needs a goal")

    db.update_agent(agent_id, status="running", last_heartbeat=db.now_iso())
    result = run_openclaw_chat(goal, url=body.url or DEFAULT_URL, timeout_sec=body.timeout_sec)

    tokens = int(result.get("token_count") or 0)
    cost = round(tokens * 0.000002, 6)
    next_spend = round(float(agent["daily_spend"]) + cost, 4)
    status = "exceeded" if next_spend >= agent["daily_cap"] and agent["daily_cap"] > 0 else "idle"
    if not result.get("ok"):
        status = "paused"

    db.update_agent(
        agent_id,
        status=status,
        daily_spend=next_spend,
        last_heartbeat=db.now_iso(),
        total_tokens=int(agent.get("total_tokens") or 0) + tokens,
        last_run_summary=(result.get("stdout") or result.get("error") or "")[:2000],
        goal=goal,
        kind=agent.get("kind") or "openclaw",
        provider="openclaw",
        model="openclaw",
    )
    record_trace(
        agent_id=agent["id"],
        agent_name=agent["name"],
        tool_called="openclaw_chat",
        prompt=goal,
        response=(result.get("stdout") or result.get("error") or "")[:4000],
        token_count=tokens,
        latency_ms=int(result.get("latency_ms") or 0),
        status="Success" if result.get("ok") else "Error",
    )
    return {
        "ok": result.get("ok"),
        "agent_id": agent_id,
        "action": "CONTINUE" if result.get("ok") else "HALT",
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
        "error": result.get("error"),
        "latency_ms": result.get("latency_ms"),
        "token_count": tokens,
        "state": status,
        "url": result.get("url"),
        "http_status": result.get("http_status"),
    }


@app.get("/")
def dashboard():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "Dashboard missing")
    return FileResponse(index)


@app.get("/docs-ui")
def docs_alias():
    return {"swagger": "/docs", "redoc": "/redoc"}
