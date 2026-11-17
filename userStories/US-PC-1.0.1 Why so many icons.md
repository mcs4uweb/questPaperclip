---
id: US-PC-1.0.1
epic: Icons
priority: P1
sprint:
status: review
blocked_by: []
tags:
  - user-story
  - paperclip
  - icons
---

# US-PC-1.0.1 — Why so many icons

**As a** developer
**I want** to know why all of these icons were created
**So that** I can target proper devices

**Blocked by:** none
**Must not:** invent a second logo; delete the live Next public set; put Android mipmaps in `web/public/`

## Files
- Existing: `web/src/app/icon.svg`, `web/src/app/apple-icon.svg`, `web/src/app/layout.tsx`, `web/public/*`, `static/favicon.svg`, `static/favicon.ico`, `static/icons/**`, `static/index.html`, `static/site.webmanifest`, `static/browserconfig.xml`, `main.py` (favicon routes)
- Create: `docs/ICONS.md` (this answer), this story file

## Acceptance
- [x] One source artwork identified (`web/src/app/icon.svg`).
- [x] Every generated file mapped to a device / client.
- [x] Dual trees explained (`web/public/` = Next :3003, `static/icons/` = FastAPI :8001).
- [x] Target matrix: local web vs PWA vs Windows tile vs future Android APK.
- [x] Operator can ignore mipmaps unless wrapping as TWA/APK.

## Test
- Open `docs/ICONS.md`. The “What to actually ship” table names the live target (local web UI).
- Confirm `web/src/app/icon.svg` is the indigo P used by `layout.tsx`.
- Confirm Android copy-ready tree is only `static/icons/android/res/` (see that folder’s README).

**PR size:** one concern: research / inventory, no runtime change.

Ticket: `TCK-104`

Back to [[USER_STORIES]]
