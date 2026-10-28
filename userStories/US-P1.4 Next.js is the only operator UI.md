---
id: US-P1.4
epic: Epic 1 — Make the product match the docs
priority: P1
sprint: 3
status: todo
blocked_by: []
tags:
  - user-story
  - paperclip
  - epic-1
---

# US-P1.4 — Next.js is the only operator UI

**As a** Quest Studio operator
**I want** one control-plane UI that matches the API
**So that** I stop using a classic dashboard that cannot run agents.

**Blocked by:** none (can land beside Epic 0; do not block jobs work)
**Must not:** add a third UI; silently POST `kind=openclaw` when the button says Hermes.

> [!bug] Current
> Create-agent modal title is "Import OpenClaw agent" and always POSTs `provider/model/kind = openclaw`, but the agents-tab CTA says "Import Hermes agent". Auto-pause on error and "Keep working dir local" are React state only. Classic `static/index.html` cannot Run Hermes/OpenClaw/Nanoclaw. There is an unused giant `paperclip_agent_control_plane.tsx` if it is still in the tree.

## Files
- Existing: `web/src/components/PaperclipControlPlane.tsx`, `web/src/lib/api.ts`, `static/index.html`, `readme.md`, `docs/SYSTEM.md`, `start-paperclip.ps1`
- Create: none

## Acceptance
- [ ] Create-agent form has a kind selector: `hermes` / `openclaw` / `nanoclaw`. The POST body matches the selected kind (provider + model included).
- [ ] Button copy matches kind. No more "Import Hermes" that creates OpenClaw.
- [ ] New-story form exposes epic, sprint, must_not, and acceptance (they are already in state).
- [ ] Auto-pause and keep-working-dir-local either persist through the API or are removed from the UI.
- [ ] Classic dashboard is frozen: banner "use http://localhost:3003" and no new features. Or FastAPI serves the Next export in prod — pick one and document it.
- [ ] Delete or quarantine unused control-plane TSX if it is not imported.

## Test
- Create Hermes agent from the modal → API row has `kind=hermes`.
- Create OpenClaw agent → `kind=openclaw`.
- Manual: classic `:8001/` still loads but tells you to use `:3003` for Run.

**PR size:** one concern: operator UI honesty.

Next: [[US-P1.5 Hygiene, Python pin, and CORS lock]]

Back to [[USER_STORIES]]
