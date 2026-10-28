---
id: US-P2.4
epic: Epic 2 — Operator quality
priority: P2
sprint: later
status: todo
blocked_by:
  - "[[US-P1.5 Hygiene, Python pin, and CORS lock]]"
tags:
  - user-story
  - paperclip
  - epic-2
---

# US-P2.4 — Auth and working-dir allowlist

**As a** operator who might one day bind past localhost
**I want** a token on `/api` and a working-dir allowlist
**So that** a runner cannot be pointed at `C:\Windows` or called from the LAN unsigned.

**Blocked by:** [[US-P1.5 Hygiene, Python pin, and CORS lock]]
**Must not:** bind `0.0.0.0` in this story; accept `**fields` raw SQL column names from the client; store the token in git.

> [!warning] Local-only is fine today. This story is the gate before any non-localhost bind.

## Files
- Existing: `main.py`, `db.py` `update_ticket` / `update_agent`, agent goal PATCH, `docs/SYSTEM.md`
- Create: env-based token check (e.g. `PAPERCLIP_TOKEN` in `.env`, already gitignored)

## Acceptance
- [ ] When `PAPERCLIP_TOKEN` is set, all `/api/*` except `/health` and `/ready` require `Authorization: Bearer …`.
- [ ] `working_dir` on create/run/goal must be under an allowlist: `C:\Projects\...`, `C:\Obsidian\...`. Anything else → 400.
- [ ] `update_ticket` / `update_agent` only accept a fixed field allowlist, not `**fields` from the request.
- [ ] `docs/SYSTEM.md` says: do not bind past 127.0.0.1 until this story is `done`.
- [ ] Token is read from the environment, never committed.

## Test
- With token set, GET `/api/agents` without header → 401; with header → 200.
- PATCH goal `working_dir=C:\Windows\System32` → 400.
- PATCH goal `working_dir=C:\Projects\TaxProgram` → 200.

**PR size:** one concern: local hardening. No port-bind change.

Back to [[USER_STORIES]]
