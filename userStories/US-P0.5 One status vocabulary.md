---
id: US-P0.5
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

# US-P0.5 — One status vocabulary

**As a** operator looking at the board
**I want** every ticket to use the same five statuses
**So that** seed tickets, heartbeats, and the two UIs do not disagree.

**Blocked by:** [[US-P0.1 Jobs table and async run]]
**Must not:** silently map unknown strings to Backlog; change agent run statuses (`idle` / `running` / `paused` / `exceeded`) in this story.

> [!bug] Current
> Board lanes: `todo` / `assigned` / `in-progress` / `review` / `done`.
> Heartbeat writes `in_progress`.
> Seed tickets use `backlog` / `assigned` / `completed`.
> Classic UI has 3 lanes; Next has 5.
> `TICKET_STATUSES` still accepts all of the old strings.

## Files
- Existing: `db.py` (`_seed_if_empty`, `create_ticket`), `main.py` (`TICKET_STATUSES`, heartbeat), `web/src/lib/api.ts`, `static/index.html`, `docs/SYSTEM.md`
- Create: none

## Acceptance
- [ ] Canonical ticket statuses are only: `todo`, `assigned`, `in-progress`, `review`, `done`.
- [ ] PUT/POST with any other string returns 400.
- [ ] Existing rows are migrated once: `backlog` → `todo`, `completed` → `done`, `in_progress` → `in-progress`.
- [ ] Heartbeat no longer writes `in_progress`.
- [ ] Seed tickets (if re-seeded) use the canonical set.
- [ ] Classic UI either uses the five lanes or is frozen and not the source of truth (see [[US-P1.4 Next.js is the only operator UI]]).

## Test
- PUT status `backlog` → 400.
- PUT status `todo` → 200 and the Next Backlog lane shows the card.
- After migrate, no ticket row still has `backlog` or `completed`.

**PR size:** one concern: ticket status enum + migrate.

Next: [[US-P1.1 Story-aware agent run]]

Back to [[USER_STORIES]]
