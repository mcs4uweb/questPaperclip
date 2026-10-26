from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Quest Paperclip",
    version="1.0.0",
    description="Local agent control plane: org, tickets, budgets, heartbeats, and traces.",
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


class Ticket(BaseModel):
    id: str
    title: str
    description: str = ""
    assignee_id: str
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    status: Literal["backlog", "assigned", "in_progress", "review", "completed"] = "backlog"
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"


class TicketStatusIn(BaseModel):
    status: Literal["backlog", "assigned", "in_progress", "review", "completed"]


class AgentStatusIn(BaseModel):
    status: Literal["idle", "running", "paused", "exceeded"]


class BudgetIn(BaseModel):
    daily_cap: float


agents_db: Dict[str, Agent] = {
    "quest": Agent(
        id="quest",
        name="Quest",
        role="Lead orchestrator",
        provider="OpenClaw / Bedrock",
        model="bedrock/grok-4-6",
        status="running",
        daily_cap=15.0,
        daily_spend=0.24,
    ),
    "video": Agent(
        id="video",
        name="Video Pipeline",
        role="Math / YouTube render queue",
        provider="local",
        model="video-use + Coqui",
        status="idle",
        daily_cap=5.0,
        reports_to="quest",
    ),
    "market": Agent(
        id="market",
        name="Market Watch",
        role="Morning stock health check",
        provider="web",
        model="research",
        status="idle",
        daily_cap=3.0,
        reports_to="quest",
    ),
}

tickets_db: Dict[str, Ticket] = {
    "TCK-101": Ticket(
        id="TCK-101",
        title="Process leftover video-use inputs",
        description="option-trading.txt is still unprocessed in video-use-Coqui\\inputs.",
        assignee_id="video",
        priority="High",
        status="backlog",
    ),
    "TCK-102": Ticket(
        id="TCK-102",
        title="Morning stock health check",
        description="JEPI, SPYI, JEPQ, QQQI, VIG, SCHD snapshot in Central Time.",
        assignee_id="market",
        priority="Medium",
        status="assigned",
    ),
    "TCK-103": Ticket(
        id="TCK-103",
        title="Keep Telegram heartbeats off",
        description="Heartbeat target stays none. Real DMs to 8856935268 still allowed.",
        assignee_id="quest",
        priority="Low",
        status="completed",
    ),
}

traces_db: List[TraceLog] = []
next_ticket = 104


def now() -> datetime:
    return datetime.now(timezone.utc)


def add_trace(**kwargs) -> TraceLog:
    trace = TraceLog(id=f"tr-{uuid4().hex[:6]}", **kwargs)
    traces_db.insert(0, trace)
    traces_db[:] = traces_db[:200]
    return trace


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": "Quest Paperclip",
        "company": "Quest Studio",
        "agents": len(agents_db),
        "tickets": len(tickets_db),
        "timestamp": now().isoformat(),
    }


@app.get("/api/company")
def company():
    spend = round(sum(a.daily_spend for a in agents_db.values()), 4)
    cap = round(sum(a.daily_cap for a in agents_db.values()), 2)
    return {
        "name": "Quest Studio",
        "goal": "Ship math-learning videos and keep investing / home-energy work organized without extra Telegram noise.",
        "daily_spend": spend,
        "daily_cap": cap,
        "active_agents": sum(1 for a in agents_db.values() if a.status == "running"),
        "open_tickets": sum(1 for t in tickets_db.values() if t.status != "completed"),
    }


@app.get("/api/agents", response_model=List[Agent])
def list_agents():
    return list(agents_db.values())


@app.patch("/api/agents/{agent_id}/status", response_model=Agent)
def set_agent_status(agent_id: str, body: AgentStatusIn):
    agent = agents_db.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.status = body.status
    return agent


@app.patch("/api/agents/{agent_id}/budget", response_model=Agent)
def set_agent_budget(agent_id: str, body: BudgetIn):
    agent = agents_db.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.daily_cap = max(0.0, body.daily_cap)
    if agent.daily_spend >= agent.daily_cap and agent.daily_cap > 0:
        agent.status = "exceeded"
    return agent


@app.post("/api/agents/{agent_id}/heartbeat")
def heartbeat(agent_id: str, body: HeartbeatIn):
    agent = agents_db.get(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    if agent.status == "paused":
        raise HTTPException(403, "Agent is paused")

    next_spend = round(agent.daily_spend + body.cost_incurred, 4)
    if next_spend > agent.daily_cap:
        agent.status = "exceeded"
        add_trace(
            agent_id=agent.id,
            agent_name=agent.name,
            tool_called="heartbeat",
            prompt=body.note or "heartbeat",
            response=f"HALT: cap ${agent.daily_cap:.2f}",
            token_count=body.tokens_consumed,
            status="Blocked by Cap",
        )
        raise HTTPException(
            403,
            f"Daily budget cap ${agent.daily_cap:.2f} reached. Agent paused.",
        )

    agent.daily_spend = next_spend
    agent.last_heartbeat = now()
    agent.status = "running"
    if body.current_task_id and body.current_task_id in tickets_db:
        tickets_db[body.current_task_id].tokens_used += body.tokens_consumed
        if tickets_db[body.current_task_id].status in ("backlog", "assigned"):
            tickets_db[body.current_task_id].status = "in_progress"

    add_trace(
        agent_id=agent.id,
        agent_name=agent.name,
        tool_called="heartbeat",
        prompt=body.note or f"task={body.current_task_id or 'none'}",
        response=f"CONTINUE remaining=${agent.daily_cap - agent.daily_spend:.2f}",
        token_count=body.tokens_consumed,
        latency_ms=42,
        status="Success",
    )
    return {
        "action": "CONTINUE",
        "agent_id": agent.id,
        "current_spend": agent.daily_spend,
        "remaining_budget": round(agent.daily_cap - agent.daily_spend, 4),
        "state": agent.status,
    }


@app.get("/api/tickets", response_model=List[Ticket])
def list_tickets():
    return list(tickets_db.values())


@app.post("/api/tickets", response_model=Ticket)
def create_ticket(body: TicketCreate):
    global next_ticket
    if body.assignee_id not in agents_db:
        raise HTTPException(400, "Unknown assignee")
    ticket_id = f"TCK-{next_ticket}"
    next_ticket += 1
    ticket = Ticket(
        id=ticket_id,
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
        priority=body.priority,
        status="backlog",
    )
    tickets_db[ticket_id] = ticket
    return ticket


@app.put("/api/tickets/{ticket_id}/status", response_model=Ticket)
def update_ticket_status(ticket_id: str, body: TicketStatusIn):
    ticket = tickets_db.get(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    ticket.status = body.status
    return ticket


@app.get("/api/traces", response_model=List[TraceLog])
def list_traces(limit: int = 50):
    return traces_db[: max(1, min(limit, 200))]


@app.get("/")
def dashboard():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "Dashboard missing")
    return FileResponse(index)


@app.get("/docs-ui")
def docs_alias():
    return {"swagger": "/docs", "redoc": "/redoc"}
