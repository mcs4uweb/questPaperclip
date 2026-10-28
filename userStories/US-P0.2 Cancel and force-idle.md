---
id: US-P0.2
epic: Epic 0 — Stop treating a run as a request
priority: P0
sprint: 1
status: todo
blocked_by:
  - "[[US-P0.1 Jobs table and async run]]"
tags:
  - user-story
  - paperclip
  - epic-0
---

# US-P0.2 — Cancel and force-idle

**As a** Quest Studio operator
**I want** one-click cancel and force-idle
**So that** a stuck Running card does not need a PowerShell PATCH.

**Blocked by:** [[US-P0.1 Jobs table and async run]]
**Must not:** leave orphan CLI processes if we can kill the job's child; invent spend; change budget math.

> [!bug] Current
> Stuck cards are reset with `PATCH /api/agents/<id>/status { "status": "idle" }`. There is no cancel. The CLI may still be running.

## Files
- Existing: `db.py`, `main.py`, `web/src/lib/api.ts`, `web/src/components/PaperclipControlPlane.tsx`, `docs/SYSTEM.md`
- Create: none unless US-P0.1 already added `jobs.py`

## Acceptance
- [ ] `POST /api/jobs/{id}/cancel` marks a queued job cancelled, or a running job cancelled and attempts to stop the child process.
- [ ] `POST /api/agents/{id}/idle` sets the agent to `idle` and cancels any open job for that agent.
- [ ] Next UI: Cancel on a running card, and Force idle when status is `running` or `paused`.
- [ ] A cancelled job writes a trace with status `Cancelled` (not Success).
- [ ] `docs/SYSTEM.md` drops the "use PowerShell PATCH" workaround as the primary fix.

## Test
- Queue a job, cancel while queued → job `cancelled`, agent `idle`.
- Force-idle while running → agent `idle`, job not left `running`.
- Manual: click Force idle on a stuck card; refresh; card is Idle.

**PR size:** one concern: cancel / idle on top of the jobs table.

Next: [[US-P0.3 Shared runner contract]]

Back to [[USER_STORIES]]
