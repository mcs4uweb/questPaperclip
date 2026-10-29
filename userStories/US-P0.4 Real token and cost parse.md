---
id: US-P0.4
epic: Epic 0 — Stop treating a run as a request
priority: P0
sprint: 2
status: review
blocked_by:
  - "[[US-P0.3 Shared runner contract]]"
tags:
  - user-story
  - paperclip
  - epic-0
---

# US-P0.4 — Real token and cost parse

**As a** Quest Studio operator
**I want** traces and daily spend to use real usage
**So that** budget caps mean something.

**Blocked by:** [[US-P0.3 Shared runner contract]]
**Must not:** invent tokens from `len(goal.split())`; invent heartbeat spend; use a magic 12.4 monthly multiplier.

> [!bug] Current
> Runners set `token_count = len(goal.split()) + len(stdout.split())` and `cost = tokens * 0.000002`. Heartbeat POSTs a hardcoded 250 tokens / $0.04. The Next monthly bar uses `daily_spend * 12.4 / overallMonthlyCap`. Daily spend never resets at midnight.

## Files
- Existing: `hermes_runner.py`, `openclaw_runner.py`, `nanoclaw_runner.py`, `main.py` heartbeat handler, `web/src/components/PaperclipControlPlane.tsx`, `docs/SYSTEM.md`
- Create: a small `usage.py` parser if that keeps runners thin

## Acceptance
- [x] Hermes usage is parsed from the session footer / provider usage when present. If missing, store `tokens=null` (or 0 with `usage_source=unknown`) — do not count words.
- [x] OpenClaw / Nanoclaw persist provider usage when the payload has it; otherwise `unknown`, not a word count.
- [x] Heartbeat does not invent 250 tokens / $0.04. If it only pings liveness, cost is 0.
- [x] `daily_spend` resets at local midnight **America/Chicago**.
- [x] Monthly cap is a stored number (company or per-agent), not `daily * 12.4`.
- [x] Budget UI shows source: parsed vs unknown.

## Test
- Parser unit tests: a sample Hermes footer → expected tokens/cost; footer-less stdout → unknown, not `len(words)`.
- After a fake midnight tick, `daily_spend` is 0 and `total_tokens` is unchanged.

**PR size:** one concern: usage truthfulness.

Next: [[US-P0.5 One status vocabulary]]

Back to [[USER_STORIES]]
