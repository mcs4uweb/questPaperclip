---
id: US-P1.2
epic: Epic 1 — Make the product match the docs
priority: P1
sprint: 3
status: todo
blocked_by:
  - "[[US-P1.1 Story-aware agent run]]"
tags:
  - user-story
  - paperclip
  - epic-1
---

# US-P1.2 — Import Obsidian user stories

**As a** Quest Studio operator
**I want** to import markdown stories from the TaxProgram and Math Quest vaults
**So that** I do not retype the backlog into Paperclip.

**Blocked by:** [[US-P1.1 Story-aware agent run]]
**Must not:** rewrite or delete vault files on import; import `USER_STORIES.md`, templates, or notes; invent story fields that are not in the file.

> [!info] Vaults
> - TaxProgram: `C:\Obsidian\TaxProgram\userStories\`
> - Math Quest: `C:\Obsidian\quest vault\Math Quest\userStories\`
> Templates: `Story Template.md` / `story template.md`. Skip `USER_STORIES.md`, `*notes*`, and `userStoriesDone\`.

## Files
- Existing: `db.py`, `main.py`, `web/src/components/PaperclipControlPlane.tsx`
- Create: `obsidian_sync.py` (parse frontmatter + As a / I want / So that)

## Acceptance
- [ ] `POST /api/stories/import` takes `{ "root": "<absolute path>" }` (or a named vault key) and creates/updates tickets from `US-*.md` / `US-M*.md`.
- [ ] Mapping: frontmatter `id` → `story_id`, title, epic, priority, sprint, status, blocked_by, must_not, files, acceptance, test.
- [ ] Re-import matches on `story_id` and updates fields; it does not create duplicates.
- [ ] Status in the vault (`todo` / `in-progress` / `done`) maps onto the canonical board statuses. Unknown status → `todo`.
- [ ] Import is allowlisted to `C:\Obsidian\...` (and maybe `C:\Projects\...\userStories`). Paths outside return 400.
- [ ] Next UI: Import from TaxProgram / Import from Math Quest buttons.

## Test
- Import a fixture markdown (copy of the TaxProgram template with a fake id) → one ticket, correct as_a / acceptance.
- Second import of the same file → still one ticket.
- Path `C:\Windows\...` → 400.

**PR size:** one concern: import only. Export is [[US-P1.3 Export story status back to Obsidian]].

Next: [[US-P1.3 Export story status back to Obsidian]]

Back to [[USER_STORIES]]
