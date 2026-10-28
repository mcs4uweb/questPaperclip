---
id: US-P2.3
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

# US-P2.3 — Agent delete and archive

**As a** Quest Studio operator
**I want** to archive seed agents that cannot run
**So that** Quest / Video Pipeline / Market Watch stop looking like live workers.

**Blocked by:** none
**Must not:** hard-delete traces; cascade-delete tickets without a confirm; invent runner wiring for display-only agents.

> [!bug] Current
> There is no delete/archive. Seed agents (Quest, Video Pipeline, Market Watch) have no real `kind` runner. Tickets still assign to them.

## Files
- Existing: `db.py`, `main.py`, `web/src/components/PaperclipControlPlane.tsx`, `web/src/lib/api.ts`
- Create: none

## Acceptance
- [ ] `POST /api/agents/{id}/archive` hides the agent from the default list (`archived_at` or `status` + filter). Traces remain.
- [ ] `DELETE /api/agents/{id}` is rejected if the agent has tickets or is running a job; otherwise allowed for unused agents.
- [ ] Next UI: Archive on the card, and a "Show archived" toggle.
- [ ] Seed agents are archived or marked display-only unless the operator assigns a real kind.
- [ ] Default GET `/api/agents` omits archived agents.

## Test
- Archive seed agent → default list hides it; GET with `?include_archived=1` still returns it.
- DELETE agent that owns a ticket → 400.
- DELETE unused agent → 200 and it is gone.

**PR size:** one concern: archive/delete.

Next: [[US-P2.4 Auth and working-dir allowlist]]

Back to [[USER_STORIES]]
