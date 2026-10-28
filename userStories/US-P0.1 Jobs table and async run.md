---
id: US-P0.1
epic: Epic 0 — Stop treating a run as a request
priority: P0
sprint: 1
status: todo
blocked_by: []
tags:
  - user-story
  - paperclip
  - epic-0
---

# US-P0.1 — Jobs table and async run

**As a** Quest Studio operator
**I want** Run Hermes / OpenClaw / Nanoclaw to queue a job and return immediately
**So that** the browser does not time out and the agent card does not stay stuck on Running.

**Blocked by:** none
**Must not:** keep waiting for the CLI inside the HTTP request; invent token or cost numbers; bind past 127.0.0.1.

> [!bug] Current
> `POST /api/agents/{id}/hermes/run`, `/openclaw/run`, and `/nanoclaw/run` all call the runner and wait. Hermes has no timeout. The browser gives up; uvicorn keeps going; the card stays `running`.

## Files
- Existing: `db.py`, `main.py`, `hermes_runner.py`, `openclaw_runner.py`, `nanoclaw_runner.py`, `docs/SYSTEM.md`
- Create: `jobs.py` (or a jobs section in `db.py`) if that keeps `main.py` smaller

## Acceptance
- [ ] A `jobs` table exists: `id`, `agent_id`, `ticket_id` (nullable), `kind`, `goal`, `cwd`, `status` (`queued` / `running` / `succeeded` / `failed` / `cancelled`), `stdout`, `stderr`, `error`, `tokens`, `cost`, `latency_ms`, `created_at`, `started_at`, `finished_at`.
- [ ] `POST /api/agents/{id}/run` (and the existing kind-specific `/run` URLs) return **202** with `{ job_id, status: "queued" }` and do not wait for the CLI.
- [ ] A worker (BackgroundTasks or a small process loop) executes one job per agent at a time.
- [ ] `GET /api/jobs/{id}` and `GET /api/agents/{id}` show live job status. Agent `status` is `running` only while a job is `running`.
- [ ] Empty goal still returns 400 before a job is created.
- [ ] Paused / over-cap agents still return 403 and do not enqueue.

## Test
- POST run without a goal → 400, no job row.
- POST run with a goal → 202 + job_id; GET job shows queued then running/succeeded/failed.
- A second POST for the same agent while a job is running is rejected or queued behind it — pick one and document it in `docs/SYSTEM.md`.

**PR size:** one concern: async jobs, not runner cleanup.

Next: [[US-P0.2 Cancel and force-idle]]

Back to [[USER_STORIES]]
