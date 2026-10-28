---
id: US-P1.6
epic: Epic 1 — Make the product match the docs
priority: P1
sprint: 2
status: todo
blocked_by:
  - "[[US-P0.1 Jobs table and async run]]"
  - "[[US-P0.4 Real token and cost parse]]"
tags:
  - user-story
  - paperclip
  - epic-1
---

# US-P1.6 — Smoke tests for health, run, and budget

**As a** maintainer
**I want** pytest + httpx coverage of the control plane
**So that** we stop shipping an untested 4k-line app.

**Blocked by:** [[US-P0.1 Jobs table and async run]], [[US-P0.4 Real token and cost parse]]
**Must not:** call a real Hermes/OpenClaw/Nanoclaw process; write tests against the live `data/paperclip.db`.

## Files
- Existing: `main.py`, `db.py`, `requirements.txt`
- Create: `tests/conftest.py`, `tests/test_health.py`, `tests/test_tickets.py`, `tests/test_run.py`, `tests/test_budget.py`

## Acceptance
- [ ] Tests use a temp SQLite file, not `data/paperclip.db`.
- [ ] Covered: `/health` (and `/ready` if present), create agent, create ticket, run rejected without goal, budget halt when spend >= cap, story status mapping (`todo` accepted, `backlog` rejected after US-P0.5).
- [ ] Runners are faked; no network to `:18789`.
- [ ] `pytest` is in requirements and documented in `readme.md`.
- [ ] `pytest` exits 0 on the new suite.

## Test
- This story *is* the test suite. Done when `pytest` is green on a temp DB.

**PR size:** one concern: first test harness.

Next: [[US-P2.1 Live job traces]]

Back to [[USER_STORIES]]
