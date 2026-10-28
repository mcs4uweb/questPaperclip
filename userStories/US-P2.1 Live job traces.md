---
id: US-P2.1
epic: Epic 2 — Operator quality
priority: P2
sprint: 4
status: todo
blocked_by:
  - "[[US-P0.1 Jobs table and async run]]"
tags:
  - user-story
  - paperclip
  - epic-2
---

# US-P2.1 — Live job traces

**As a** Quest Studio operator
**I want** to watch runner output while a job is in flight
**So that** empty stdout + ok:true is not a silent failure.

**Blocked by:** [[US-P0.1 Jobs table and async run]]
**Must not:** block the HTTP request again; dump secrets from `.env` into traces.

> [!bug] Current
> Traces are written only when the runner returns. Empty stdout + `ok: true` looks like success. The Next traces tab is a table + modal of `selectedTrace.response`.

## Files
- Existing: `main.py`, jobs worker from US-P0.1, `web/src/components/PaperclipControlPlane.tsx`, `web/src/lib/api.ts`
- Create: none if SSE/polling can hang off `/api/jobs/{id}`

## Acceptance
- [ ] While a job is `running`, stdout/stderr chunks are appended on the job row (or a `job_logs` table).
- [ ] Next traces / job panel polls `GET /api/jobs/{id}` (or SSE) at a modest interval and shows live text.
- [ ] A finished job with empty stdout is labeled "no output captured" — not Success with a blank body.
- [ ] Trace search still works on the finished snapshot.

## Test
- Fake runner that prints two lines one second apart → GET job after 1.5s contains the first line before the job finishes.
- Fake runner that exits 0 with empty stdout → UI/API mark output as empty, not a silent Success.

**PR size:** one concern: live logs.

Next: [[US-P2.2 Supervise uvicorn in start-paperclip.ps1]]

Back to [[USER_STORIES]]
