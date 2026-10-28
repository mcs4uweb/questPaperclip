---
id: US-P1.5
epic: Epic 1 — Make the product match the docs
priority: P1
sprint: 3
status: todo
blocked_by:
  - "[[US-P1.4 Next.js is the only operator UI]]"
tags:
  - user-story
  - paperclip
  - epic-1
---

# US-P1.5 — Hygiene, Python pin, and CORS lock

**As a** maintainer
**I want** a clean, pinned, local-only repo
**So that** the feature branch is safe to commit when asked.

**Blocked by:** [[US-P1.4 Next.js is the only operator UI]]
**Must not:** commit `data/paperclip.db`; commit or push unless the user asks; bind past 127.0.0.1.

> [!bug] Current
> `.gitignore` already ignores `__pycache__/` and `*.db`, but a `.pyc` has been tracked. CORS is `allow_origins=["*"]` + `allow_credentials=True` (invalid combo). Python 3.11 bytecode exists while 3.13 is on PATH. No `requirements` pin story beyond installing whatever is listed.

## Files
- Existing: `.gitignore`, `main.py` (CORS), `requirements.txt`, `readme.md`
- Create: `.python-version` or a note in `readme.md` stating the supported CPython

## Acceptance
- [ ] Tracked `__pycache__` / `*.pyc` are `git rm --cached` (no commit unless asked).
- [ ] CORS origins are the local UIs only (`http://127.0.0.1:3003`, `http://localhost:3003`, `http://127.0.0.1:8001`). `allow_credentials` is false unless we actually use cookies.
- [ ] Supported Python is written down (prefer 3.11 or 3.13 — pick the one `uvicorn` is already running) and `requirements.txt` is pinned enough to reinstall.
- [ ] `GET /ready` reports API up plus hermes / openclaw / nanoclaw availability (without running a model).
- [ ] `readme.md` / `docs/SYSTEM.md` mention `/ready`.

## Test
- OPTIONS/GET from an origin not in the list is not granted `*`.
- `/ready` returns JSON with three boolean availability flags.

**PR size:** one concern: hygiene + local CORS + ready. Tests themselves are [[US-P1.6 Smoke tests for health, run, and budget]].

Next: [[US-P1.6 Smoke tests for health, run, and budget]]

Back to [[USER_STORIES]]
