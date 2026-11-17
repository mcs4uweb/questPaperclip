# Quest Paperclip icons — what to target

There is **one** mark: indigo rounded square + light P.

Source artwork: `web/src/app/icon.svg` (same pixels as `web/src/app/apple-icon.svg` and `static/favicon.svg`).

Everything else is a **size or format a specific client refuses to share**. You do not ship the whole pile to every device.

Generated 2026-11-15 from that SVG. Ticket: TCK-104 / [[US-PC-1.0.1 Why so many icons]].

---

## What to actually ship

| Target | Keep | Ignore |
|---|---|---|
| Local web UI only (this repo today) | SVG + ICO + 16/32 PNG + apple-touch 180 | Android `mipmap-*`, maskable 192/512 |
| Installable PWA / “Add to Home screen” | above + 192/512 + maskable + `site.webmanifest` | Android `mipmap-*` |
| Windows Start / pinned Edge | `mstile-150x150.png` + `browserconfig.xml` | Android `mipmap-*` |
| Native Android / TWA / Play later | copy `static/icons/android/res/` into `app/src/main/res/` | web favicons |

Today Paperclip is two localhost UIs (`:3003` Next, `:8001` classic). Treat **local web UI** as the live target. The mipmap tree is inventory for a future APK, not something the browser loads.

---

## Why two copies of the web set

| Tree | Server | Why |
|---|---|---|
| `web/public/` | Next.js `:3003` | files are served from `/` |
| `static/` + `static/icons/` | FastAPI `:8001` | same pixels, different origin |

Same artwork. Two processes. See [[US-P1.4 Next.js is the only operator UI]] — when classic UI dies, delete the `static/` copies, not the Next set.

Android launcher assets live only under `static/icons/android/` (not duplicated into `web/public/`).

---

## Browsers / tabs

| File | Size | Device / client | Why it exists |
|---|---|---|---|
| `web/src/app/icon.svg` | vector | Next tab (App Router) | source + sharp at any zoom |
| `web/src/app/apple-icon.svg` | vector | Next iOS fallback | App Router apple icon convention |
| `static/favicon.svg` | vector | classic UI tab | FastAPI has no App Router |
| `web/public/favicon.ico` / `static/favicon.ico` | 16 / 32 / 48 | old tabs, bookmarks, Windows taskbar | many clients still request `/favicon.ico` and ignore SVG |
| `favicon-16x16.png` | 16 | Chrome/Firefox pinned tab, bookmarks | explicit PNG when SVG/ICO is ignored |
| `favicon-32x32.png` | 32 | retina tab / Windows shortcut overlay | same |
| `favicon-48x48.png` | 48 | Windows site icon / some Chromium lists | same |

Wired in `web/src/app/layout.tsx` and `static/index.html`. FastAPI also serves `/favicon.svg` and `/favicon.ico` from `main.py`.

---

## Phones / tablets (Add to Home screen)

| File | Size | Device / client | Why it exists |
|---|---|---|---|
| `apple-touch-icon.png` | 180 | iOS / iPadOS Safari | Apple does **not** use `favicon.ico`. Home-screen + share sheet. |
| `android-chrome-192x192.png` | 192 | Chrome Android, PWA | minimum installable-PWA icon |
| `android-chrome-512x512.png` | 512 | Chrome Android, PWA splash | Play / install splash |
| `android-chrome-maskable-192x192.png` | 192 | Android adaptive crop | safe-zone version; without it the P is clipped into a circle/squircle |
| `android-chrome-maskable-512x512.png` | 512 | same, high-dpi | same |
| `site.webmanifest` | — | Android Chrome | tells the OS which of those PNGs to use |
| `mstile-150x150.png` | 150 | Windows Start / pinned Edge | Microsoft tile, not a favicon |
| `browserconfig.xml` | — | Windows / Edge | points at the mstile + tile color `#4338ca` |

Manifest icons (Next): `/android-chrome-*.png`. Classic UI prefixes `/icons/`.

---

## Native Android (only if you wrap Paperclip as an APK / TWA)

Copy **`static/icons/android/res/`** into `app/src/main/res/`. Do not copy the sibling `static/icons/android/mipmap-*` folders — those are a leftover duplicate of the same PNGs without the XML.

| Path | Size (px) | Device | Why |
|---|---|---|---|
| `res/mipmap-mdpi/ic_launcher.png` | 48 | ~160 dpi phones | legacy square launcher |
| `res/mipmap-hdpi/ic_launcher.png` | 72 | ~240 dpi | same |
| `res/mipmap-xhdpi/ic_launcher.png` | 96 | ~320 dpi | same |
| `res/mipmap-xxhdpi/ic_launcher.png` | 144 | ~480 dpi | same |
| `res/mipmap-xxxhdpi/ic_launcher.png` | 192 | ~640 dpi | same |
| `res/mipmap-*/ic_launcher_round.png` | same as above | pre-Android 8 | round launcher, before adaptive icons |
| `res/mipmap-mdpi/ic_launcher_foreground.png` | 108 | API 26+ | adaptive foreground (108dp, 18% padding) |
| `res/mipmap-hdpi/ic_launcher_foreground.png` | 162 | API 26+ | same |
| `res/mipmap-xhdpi/ic_launcher_foreground.png` | 216 | API 26+ | same |
| `res/mipmap-xxhdpi/ic_launcher_foreground.png` | 324 | API 26+ | same |
| `res/mipmap-xxxhdpi/ic_launcher_foreground.png` | 432 | API 26+ | same |
| `res/mipmap-anydpi-v26/ic_launcher.xml` | — | Android 8+ | adaptive square: foreground + `#4338CA` |
| `res/mipmap-anydpi-v26/ic_launcher_round.xml` | — | Android 8+ | adaptive round |
| `res/values/colors.xml` | — | Android 8+ | `ic_launcher_background` = `#4338CA` |
| `res/drawable/ic_launcher_background.xml` | — | Android 8+ | optional indigo gradient background |

Densities exist because Android picks **one** mipmap folder per device. A single 192px file would look soft on xxxhdpi and huge on mdpi.

More detail: `static/icons/android/README.md`.

---

## Why the pile looks large

- **1 artwork** × **~8 web sizes** × **2 servers** = the `web/public` + `static/icons` twins.
- **3 launcher shapes** (square, round, adaptive-foreground) × **5 densities** = the mipmap tree.
- Plus XML/manifest files that only name the PNGs.

Most files exist because **each platform refuses the others**:

- iOS ignores `.ico`
- old Windows ignores `.svg`
- Android PWA crops non-maskable icons
- Android launchers need per-density mipmaps
- Adaptive icons need a padded foreground, not the same square used in a browser tab

---

## Do not

- Do not invent a second logo. Re-export from `web/src/app/icon.svg`.
- Do not put mipmaps in `web/public/` — browsers never read them.
- Do not delete the Next public set to “clean up”; that is the live `:3003` favicon.
- Do not treat HTTP 200 on `/favicon.ico` as proof the tab updated — hard-refresh; browsers cache favicons aggressively.
