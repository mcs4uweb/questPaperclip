---
id: US-P1.3
epic: Epic 1 — Make the product match the docs
priority: P1
sprint: 3
status: todo
blocked_by:
  - "[[US-P1.2 Import Obsidian user stories]]"
tags:
  - user-story
  - paperclip
  - epic-1
---

# US-P1.3 — Export story status back to Obsidian

**As a** Quest Studio operator
**I want** Paperclip ticket status (and a short trace pointer) written back to the vault note
**So that** Obsidian stays the source of truth I read later.

**Blocked by:** [[US-P1.2 Import Obsidian user stories]]
**Must not:** rewrite the whole note; move files to `userStoriesDone` unless the user asks; touch TaxProgram or Math Quest notes that were not imported.

## Files
- Existing: `obsidian_sync.py` (from US-P1.2), `main.py`, vault notes under the two `userStories\` folders
- Create: none if export can live next to import

## Acceptance
- [ ] `POST /api/stories/export` updates only the YAML `status` (and optionally a `paperclip_ticket` / last-trace line) on notes that were imported.
- [ ] Board `review` maps to vault `in-progress` plus a visible "Review required" marker, or to `status: review` if we extend the vault convention — pick one and document it on [[USER_STORIES]].
- [ ] Failed export (file missing, vault locked) returns which story failed; others still write.
- [ ] Dry-run flag lists planned writes and changes nothing.

## Test
- Import fixture → move ticket to `done` → export → fixture frontmatter `status: done`.
- Dry-run after a status change → response lists the file, file on disk unchanged.

**PR size:** one concern: status export.

Next: [[US-P1.4 Next.js is the only operator UI]]

Back to [[USER_STORIES]]
