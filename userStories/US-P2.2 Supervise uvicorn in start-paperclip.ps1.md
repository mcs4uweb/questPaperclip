---
id: US-P2.2
epic: Epic 2 — Operator quality
priority: P2
sprint: 4
status: todo
blocked_by: []
tags:
  - user-story
  - paperclip
  - epic-2
---

# US-P2.2 — Supervise uvicorn in start-paperclip.ps1

**As a** operator who logs into Windows
**I want** Paperclip to stay up and leave logs I can read
**So that** a hidden crashed uvicorn is obvious.

**Blocked by:** none
**Must not:** start uvicorn on `0.0.0.0`; hide crashes with no log line.

> [!bug] Current
> `start-paperclip.ps1` fire-and-forgets a hidden `Start-Process` with no stdout capture. If the process dies later, the scheduled task does not restart it. Next.js is not started.

## Files
- Existing: `start-paperclip.ps1`, `readme.md`, `docs/SYSTEM.md`
- Create: none (or a tiny `watch-paperclip.ps1` if that is cleaner)

## Acceptance
- [ ] uvicorn stdout/stderr append to `C:\Projects\logs\paperclip-yyyy-MM-dd.log` (already the intended log path).
- [ ] If port 8001 is not listening after start, the script logs the failure and exits non-zero.
- [ ] Optional: scheduled-task friendly "already running" remains exit 0, but a dead PID occupying nothing is restarted.
- [ ] Document how to also start Next on :3003 (optional flag, not required at logon).
- [ ] Still binds `127.0.0.1` only.

## Test
- Manual: run the script twice — second run exits 0 and does not start a second listener.
- Manual: stop uvicorn, run the script — port 8001 listens and the log file has the start line.

**PR size:** one concern: process supervision.

Next: [[US-P2.3 Agent delete and archive]]

Back to [[USER_STORIES]]
