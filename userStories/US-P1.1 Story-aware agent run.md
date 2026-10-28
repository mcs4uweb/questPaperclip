---
id: US-P1.1
epic: Epic 1 — Make the product match the docs
priority: P1
sprint: 2
status: todo
blocked_by:
  - "[[US-P0.1 Jobs table and async run]]"
  - "[[US-P0.5 One status vocabulary]]"
tags:
  - user-story
  - paperclip
  - epic-1
---

# US-P1.1 — Story-aware agent run

**As a** Quest Studio operator
**I want** "Run agent on this story" to send the story, not the agent's leftover goal
**So that** the board actually drives work.

**Blocked by:** [[US-P0.1 Jobs table and async run]], [[US-P0.5 One status vocabulary]]
**Must not:** start the next epic's stories; invent acceptance text; commit or push without being asked.

> [!bug] Current
> `docs/SYSTEM.md` says Run-on-story still uses the **agent goal**. The Next button does the same. Moving a lane does not start an agent.

## Files
- Existing: `main.py`, `web/src/components/PaperclipControlPlane.tsx`, `web/src/lib/api.ts`, `docs/SYSTEM.md`
- Create: a small prompt composer if that keeps the UI thin

## Acceptance
- [ ] Run-on-story composes the job goal from `story_id`, title, as_a / i_want / so_that, acceptance, must_not, files, and `working_dir`.
- [ ] On start: ticket → `in-progress`. On job success: ticket → `review`. On failure: ticket stays `in-progress` and the card shows the error.
- [ ] The agent card goal is not overwritten unless the operator edits it.
- [ ] Job row stores `ticket_id`.
- [ ] `docs/SYSTEM.md` no longer says "put the story id into the goal yourself".

## Test
- POST run with `ticket_id` of a todo story → job prompt contains the story id and acceptance; ticket is `in-progress`.
- Failed job → ticket still `in-progress`, not `review` or `done`.

**PR size:** one concern: story → job prompt + status moves.

Next: [[US-P1.2 Import Obsidian user stories]]

Back to [[USER_STORIES]]
