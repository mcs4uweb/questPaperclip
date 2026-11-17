# Android launcher icons (Quest Paperclip)

Copy `res/` into an Android app module (`app/src/main/res/`).

Generated from the P-mark SVG (`web/src/app/icon.svg`): indigo rounded square, light P.

## Contents

| Path | Size | Use |
|---|---|---|
| `res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png` | 48 / 72 / 96 / 144 / 192 | Legacy square launcher |
| `res/mipmap-*/ic_launcher_round.png` | same | Round launcher (pre-adaptive) |
| `res/mipmap-*/ic_launcher_foreground.png` | 108 / 162 / 216 / 324 / 432 | Adaptive foreground (108dp, 18% safe zone) |
| `res/mipmap-anydpi-v26/ic_launcher.xml` | adaptive | API 26+ square |
| `res/mipmap-anydpi-v26/ic_launcher_round.xml` | adaptive | API 26+ round |
| `res/values/colors.xml` | `#4338CA` | Adaptive background color |
| `res/drawable/ic_launcher_background.xml` | indigo gradient | Optional adaptive background drawable |

Play / Chrome store assets (also in `static/icons/` and `web/public/`):

- `android-chrome-192x192.png`
- `android-chrome-512x512.png`
- `android-chrome-maskable-192x192.png`
- `android-chrome-maskable-512x512.png`
