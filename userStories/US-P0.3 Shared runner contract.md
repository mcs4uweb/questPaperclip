---
id: US-P0.3
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

# US-P0.3 — Shared runner contract

**As a** maintainer
**I want** Hermes, OpenClaw, and Nanoclaw to share one run contract
**So that** cap checks, status writes, and traces are not copy-pasted three times.

**Blocked by:** [[US-P0.1 Jobs table and async run]]
**Must not:** add a fourth agent kind; guess more OpenClaw JSON shapes; invent token counts.

> [!bug] Current
> `run_hermes_agent`, `run_openclaw_agent`, and `run_nanoclaw_agent` in `main.py` each reimplement paused/cap checks, spend math (`tokens * 0.000002`), status writes, and traces. OpenClaw still tries several payload shapes.

## Files
- Existing: `main.py`, `hermes_runner.py`, `openclaw_runner.py`, `nanoclaw_runner.py`
- Create: `runner.py` (or similar) with `run_agent(agent, goal, cwd) -> Result`

## Acceptance
- [ ] One `Result` type: `ok`, `stdout`, `stderr`, `error`, `tokens`, `cost`, `latency_ms`, `model`.
- [ ] Cap / pause / goal / trace / spend updates live in one function used by all three kinds.
- [ ] Kind-specific `/hermes/run`, `/openclaw/run`, `/nanoclaw/run` become thin aliases of `POST /api/agents/{id}/run`.
- [ ] OpenClaw pins **one** request payload and fails with the HTTP status + first 500 chars of body if it does not match.
- [ ] Seed display-only agents (Quest, Video Pipeline, Market Watch) are not silently routed through a real CLI unless `kind` is `hermes` / `openclaw` / `nanoclaw`.

## Test
- Unit-test the shared Result mapping with a fake runner (ok / fail / empty stdout).
- OpenClaw unknown JSON → `ok: false` and a readable error, not a guessed empty success.

**PR size:** one concern: one runner path. Do not also parse real tokens here ([[US-P0.4 Real token and cost parse]]).

Next: [[US-P0.4 Real token and cost parse]]

Back to [[USER_STORIES]]
