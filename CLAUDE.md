# Notes for Claude sessions

Zepp OS watch faces for the Amazfit Balance 3 (480×480 round). Sextant is the first face; Twisted Sextant (draft) is Sextant's code and generator with overrides (`faces/twisted-sextant/design/variant.json`), so changes to Sextant apply to both. The canonical guide is `docs/development.md`, so read it before changing anything. This file is the short version of what a new session needs.

## How we work

- Sessions can push to this repo (the owner granted access to `raetha/zepp-watch-faces` only), so commit and push to `main` when a piece of work is done. If a session has read-only access, fall back to a zip of the repo (`docs/development.md` → "Packaging for delivery").
- Each push to `main` publishes DEV test builds at https://raetha.github.io/zepp-watch-faces/dev/, and the owner tests them on the watch.
- A version bump in a face's `app.json` on `main` publishes a release, so never bump a version or date a changelog without being asked. Record changes under `## [Unreleased]` in `faces/<face>/CHANGELOG.md`.
- Licences: `lib/` and `tools/` are MIT. `faces/<face>/` is CC BY-NC-SA 4.0. Fonts are OFL. Face artwork is original, so never copy other faces.

## Validate on the real firmware, not just the harness

- `npm test` and `npm run previews` are the fast offline loop: a stubbed runtime plus approximate renders. Use them for prototyping.
- Use the emulator for validation and screenshots. It runs the real Zepp OS firmware (Balance 2 image) in QEMU, headless.
- First-time setup in a fresh container (about 5 minutes, about 240 MB download):

  ```bash
  apt-get install -y libvte-2.91-0 libaio1t64 xvfb xdotool
  pip install --break-system-packages -r tools/requirements.txt
  npm install && npm install -g @zeppos/zeus-cli@1.9.3
  node tools/emu/emu.mjs setup
  node tools/emu/emu.mjs start && node tools/emu/emu.mjs enable-aod && node tools/emu/emu.mjs save-base
  ```

- Network allowlist needed: `*.zepp.com` and `*.huami.com`. That covers Zeus builds, `upload-cdn.zepp.com` (emulator and firmware) and `upload-cdn.huami.com` (device list). Node's `fetch` ignores the proxy, so the tools download with `curl`.
- Loop: `node tools/emu/emu.mjs start`, then `install <face>`, then `set k=v …`, then `shot out.png`. Look at the PNG.
- `npm run screenshots -- <face>` retakes the README screenshots (about 7 minutes) from `faces/<face>/emu-shots.json`.
- The emulated watch has quirks (buttons, scrolling, screen timeout, settings applying at the minute tick). They're documented in `docs/development.md` → "Testing on the emulator", so read that before scripting new interactions.

## Hard-won facts (details in docs/development.md)

- A `.zab` holds one `.zpk` per screen and chip. `tools/extract_zpk.py` must pick by device ID (Balance 3 = 11141376), not take the first one.
- The emulator can't decode `zeus build`'s compressed images. `tools/emu/prepare.py` swaps the PNGs back in.
- Faces target API level 4.2 (`@zos/*` modules), the highest the Balance 2 emulator image runs. **When Zepp publishes a Balance 3 emulator image, move to 4.4 (or whatever is current).**
- Face code can't read floors, the current weather, UV, humidity or air quality at any API level. They're bound widgets (`TEXT_FONT` / `IMG_LEVEL` with a data type).
- The emulator only feeds test values to steps, calories, heart rate and battery reads; the other sensors read 0 there. `DEMO_VALUES` (a generator override) fakes readings for mock-ups.
- Both designs are locked (2026-10-18): there are no switches for alternative designs. Try ideas with `SEXTANT_OVERRIDES` mock-ups; the dropped alternatives are listed in `faces/sextant/docs/design.md` and live in git history.
- Editor type numbers come from `METRIC_TYPE` in `lib/js/metrics.js` and must never change; append new metrics.
- Text boxes must sit on whole pixels. Arc `radius` is the centre of the stroke.
- Arc angles are truncated to whole degrees, and arcs under 1° don't draw. Ticks use `geometry.tick_arc()`.
- Edit mode shows only `ONLY_EDIT` widgets and the edit groups, in creation order.
