# Developing watch faces in this repo

This is the canonical guide for the repository. Read it before changing anything.

## Layout

| Path | What it is |
| --- | --- |
| `faces/<face>/app.json`, `app.js` | Zepp OS manifest and app entry for one face (watch face, API level 4.2). |
| `faces/<face>/watchface/index.js` | The face's code: edit groups, widgets per theme, updates. |
| `faces/<face>/watchface/layout.generated.js` | **Generated.** Every coordinate, colour and size the face uses. |
| `faces/<face>/assets/common.r/` | **Generated.** PNGs plus the subset font for text widgets. `icon.png` and `cover.png` come from `npm run screenshots` (the emulator's `day.png`). |
| `faces/<face>/design/` | The face's generator: `config.py` (design constants), `geometry.py`, `assets.py`, `generate.py`. |
| `faces/<face>/scenarios/` | Harness scenarios (sensor values, editor picks, expected theme). |
| `faces/<face>/CHANGELOG.md` | The face's version history; its sections become the GitHub release notes. |
| `faces/<face>/screenshots/` | README screenshots, taken on the real firmware by `npm run screenshots` from `emu-shots.json`. |
| `faces/<face>/previews/` | Quick offline renders from `npm run previews` (not committed; for prototyping). |
| `faces/<face>/docs/` | The install QR code and design notes. |
| `lib/js/` | Shared runtime helpers: `format.js`, `sun.js` (sunrise, sunset, night detection), `metrics.js` (complication definitions). |
| `lib/py/zfkit/` | Shared generator helpers: `fonts.py` (instancing, subsetting, text-box maths), `icons.py` (original icon artwork). |
| `tools/emu/` | Runs faces on the real Zepp OS firmware in QEMU (see "Testing on the emulator"). |
| `tools/` | `generate.py` (all faces), `harness/` (offline runner), `preview.py`, `make_covers.py`, `make_qr.py`, `extract_zpk.py`, `build_site.py`, `new_face.py`, and the release helpers `release_plan.py`, `changelog.py`, `release_notes.py`. |
| `fonts/` | OFL variable fonts (Roboto, Roboto Condensed) and their licences. |

Faces import shared JS with relative paths, for example `import { isNight } from '../../../lib/js/sun';`. Zeus bundles these when building the face.

**Variant faces.** Twisted Sextant (`faces/twisted-sextant/`) has no design or face code of its own. Its `design/generate.py` runs Sextant's generator with `SEXTANT_FACE_DIR` pointing at it and the overrides in its `design/variant.json`, and its `watchface/index.js` calls `sextantFace(LAYOUT)` from `faces/sextant/watchface/sextant.js`. Layout options the shared code reads: `edit_metrics` (the metrics editable slots offer) and `fixed_slots` (slots that aren't editable). Regenerate both faces after changing Sextant's design (`npm run assets`).

## One-time setup

```bash
pip install -r tools/requirements.txt     # pillow, cairosvg, fonttools, numpy, qrcode
npm install                               # esbuild for the harness
npm install -g @zeppos/zeus-cli           # only needed to build/preview on a watch
```

## Everyday loop

1. Change a face's design constants in `faces/<face>/design/config.py`, or its drawing code.
2. `npm run assets` (or `python3 faces/<face>/design/generate.py`) regenerates its assets and `layout.generated.js`.
3. `npm test` runs every scenario of every face through the real watch-face code against stubbed Zepp OS modules (`@zos/ui`, `@zos/sensor`, `@zos/settings`, `@zos/utils`). It fails on:
   - runtime errors,
   - missing assets,
   - the wrong theme for a scenario (a scenario's `expect_theme`, default `color`).
4. `npm run previews` renders quick approximations of every scenario (normal, always-on and edit mode) to `faces/<face>/previews/`. They're for trying ideas fast, without the emulator.
5. **Validate on the real firmware** (see "Testing on the emulator"): `npm run emu -- start`, then `npm run emu -- install <face>`, then `npm run emu -- shot out.png`.
6. `npm run screenshots -- <face>` retakes the README screenshots on the emulator and refreshes `icon.png` and `cover.png`. Do this before a release.
7. On your own watch: push to `main` and scan the test build's QR code (see "Test builds").

Never hand-edit `layout.generated.js` or anything under `assets/common.r/`. They are overwritten on the next generate.

## Adding a new face

```bash
npm run new-face -- harbor --title "Harbor"
```

This copies Sextant's code, generator and scenarios (not its screenshots) to `faces/harbor/`, with a fresh `appId`, version 0.1.0, a starter `CHANGELOG.md`, and a `DRAFT` marker so it isn't released yet. Then:

1. Rework `faces/harbor/design/` and `faces/harbor/watchface/index.js`.
2. Run `npm run assets && npm test && npm run previews`, then check it on the emulator. Copy and adapt `emu-shots.json` and run `npm run screenshots -- harbor`.
3. Run `npm run qr -- harbor` to create `faces/harbor/docs/install-qr.png`.
4. Add a `README.md` and `LICENSE` for the face (copy Sextant's and change the name), and add a row to the root README's table.
5. When it's ready, date its `0.1.0` changelog entry, delete `DRAFT` and push. That publishes the first release.

If more than one face needs a piece of code, move it to `lib/js/` or `lib/py/zfkit/` instead of copying it.

## How Sextant is built (reference for new faces)

- **API level 4.2** (`app.json` → `runtime.apiVersion`). The face imports `@zos/ui`, `@zos/sensor`, `@zos/settings` and `@zos/utils`, and lists a permission for each health sensor it reads (`data:user.hd.step` and so on). 4.2 is the highest level the emulator runs (Balance 2 image); the Balance 3 itself is 4.4. **When Zepp publishes a Balance 3 emulator image, move to 4.4 (or whatever is then current)**, retest and update this note.

- **Edit groups** are created once in `build()`: five complication slots, a theme picker (Color / Mono) over the date, and a night-mode switch (Auto / Off) over the time. They use custom edit types (`100001+`), so any metric can go in any slot.
- **`render(theme)`** creates every visible widget for `color`, `mono` or `night`. Night runs from sunset to sunrise (forecast sun data, or 19:00–07:00 until that exists). On a theme change, the rendered widgets are deleted and recreated. Sensors, listeners and the `WIDGET_DELEGATE` are created once and never deleted.
- **Weather**: as a complication (default top-middle), the icon is an `IMG_LEVEL` bound to `WEATHER_CURRENT` and the temperature is a bound `TEXT_FONT`. The condition text under the time is another `IMG_LEVEL`, with one image per condition. The condition names are pre-rendered text images. Face code can't read the current condition, so this is the only way to show it.
- **Arc angles are whole degrees.** The firmware truncates `start_angle`, `end_angle` and the level-filled end to whole degrees, and arcs under 1° don't draw. `geometry.tick_arc()` gives each tick integer angles, extending away from the nearer centre-line point, so the bezel is symmetric both ways. The preview truncates the same way.
- **Gauges**: every tick is its own short `ARC_PROGRESS` (one per 2°, coloured dim or lit), so nothing depends on how the firmware layers arcs over images. An earlier overlay-mask approach failed on the Balance 3: arcs drew on top of the mask.
  - Sensor metrics with a goal (steps, calories, PAI, stand, fat burning) light the first round(progress × N) ticks in fill order.
  - System-bound metrics (floors, current weather, UV, humidity, air quality) have no sensor at API level 4.2. They show their value through `TEXT_FONT`, and the face can't read the number, so floors' ticks stay dim.
- **Metrics** are defined once in `lib/js/metrics.js`: `METRIC_IDS` is the editor order, and `METRIC_TYPE` gives each metric a fixed editor type number (100001 + n), so reordering or adding metrics never changes what a saved slot shows. Add new metrics at the end of `METRIC_TYPE`. Each metric also needs a colour and title in `design/config.py` (`METRICS`), an icon in `lib/py/zfkit/icons.py`, a sample in the edit previews, and a permission in `app.json` if its sensor needs one. Units drawn small after the value are listed in `UNIT_CHARS`. Moon phase is computed from the date (`lib/js/moon.js`). The compass only runs while a slot shows it and the face is on screen.
- **Editor:** the firmware draws it. Tapping a selected box steps to the next option, and swiping up or down on it (or turning the crown) scrolls through them. A face can't replace it with a full-screen list.
- **Text** is `TEXT` / `TEXT_FONT` with the bundled Roboto Condensed. The time is `IMG_TIME` with pre-rendered fixed-width digits (Roboto Regular, size solved from `TIME_SIDE_GAP`, currently 106px, brass gradient).
- **Always-on** widgets use `show_level: ONLY_AOD`: outline digits, date and battery.

## Testing on the emulator

`tools/emu/emu.mjs` runs a face on the real Zepp OS firmware, headless, using the QEMU emulator that ships with Zepp's simulator. The image is the Amazfit Balance 2 (480×480 round, Zepp OS 5), the closest one Zepp publishes to the Balance 3. It's the same firmware a watch runs, so it shows what the offline harness can only approximate:
- real text placement and arc drawing,
- edit mode,
- data binding (weather, floors and so on),
- night mode from the forecast's sun times.

One-time setup (Linux x86_64, about 5 minutes). It downloads about 240 MB from Zepp's CDN into `tools/.emu/`, which isn't committed.

```bash
sudo apt-get install -y libvte-2.91-0 libaio1t64 xvfb xdotool   # QEMU's libraries, virtual display, touch input
npm install                                                     # ws (talks to the emulated watch)
npm install -g @zeppos/zeus-cli                                  # builds the face
node tools/emu/emu.mjs setup                                     # emulator + Balance 2 firmware
node tools/emu/emu.mjs start                                     # boot a factory-fresh watch (about 40 s)
node tools/emu/emu.mjs enable-aod                                # turn the always-on screen on (scheduled 08:00-22:00)
node tools/emu/emu.mjs save-base                                 # keep this watch state as tools/.emu/base-flash.bin
```

Network access needed: `upload-cdn.zepp.com` and `upload-cdn.huami.com` (emulator, firmware, device list), plus whatever Zeus uses on `*.zepp.com` / `*.huami.com` while building. In a Claude session these must be allowed in the session's network settings.

Everyday commands (`npm run emu -- <command>` works too):

```bash
node tools/emu/emu.mjs reset                          # restore base-flash.bin (do this for a known state)
node tools/emu/emu.mjs start --time 2026-10-15T10:08:00   # boot with the clock at this time (UTC); 21:14 for night mode
node tools/emu/emu.mjs install sextant                # zeus build + install + make it the active face
node tools/emu/emu.mjs set walkstep=12486 goal_walkstep=15000 btcon=false weather=3 temp=18
node tools/emu/emu.mjs shot out.png                   # 480x480 screenshot
node tools/emu/emu.mjs tap 240 240 2.5                # long-press: face picker; then tap 240 438 for Edit
node tools/emu/emu.mjs tap 240 105                    # in Edit: tap a box to select it, tap again to cycle options
node tools/emu/emu.mjs key ret                        # leave Edit
node tools/emu/emu.mjs rest                           # screen off: the always-on view
node tools/emu/emu.mjs face                           # back to the watch face
node tools/emu/emu.mjs stop
```

**Spacing check:** `python3 tools/emu/audit.py faces/sextant shot.png` measures each complication's icon and value centring and gaps, plus the battery, the date, the status-icon row and the condition text, on an emulator screenshot.

**Mock-ups:** `SEXTANT_OVERRIDES='{"KEY": value}' python3 faces/sextant/design/generate.py` builds a variant from any `config.py` constants without editing the file. Install it on the emulator and screenshot it for side-by-side comparisons.

**Screenshots:** `npm run screenshots -- <face>` runs `tools/emu/screenshots.mjs`, which follows `faces/<face>/emu-shots.json`:
- each run resets the watch, boots at a set time, installs the face and applies the values;
- steps take shots, take always-on shots, open the editor and cycle options;
- the results land in `faces/<face>/screenshots/`.

Only shots the READMEs or the install site use are kept. A full Sextant set takes about 6 minutes. `--run N` redoes one run.

**How the emulated watch behaves** (Balance 2 v1.1.0 image), which the scripts rely on:
- **Buttons:**
  - `key ret` selects. It also leaves the watch-face editor.
  - `key home` (upper button) and `key backspace` (lower button) both toggle between the face and the app list.
  - In Settings, back is a swipe from the left edge: `swipe 5 240 300 240`.
  - `face` checks the screen before pressing anything.
- **Touch** goes through QEMU's GTK window on the virtual display `:99`. That's why it needs Xvfb and xdotool, and why `-display none` can't be used. Monitor-injected mouse events don't reach the firmware.
- **Scrolling:** a fast swipe flings a list. `swipe x1 y1 x2 y2 1200` drags slowly and scrolls exactly the distance moved.
- **Arcs are whole degrees.** Angles are truncated, and arcs under 1° don't draw. Measure positions around the true screen centre (pixel 239.5) when checking symmetry.
- **Unchanged values:** `set` with the same weather values as before doesn't refresh the weather, and the DND state can stick. Change a value to force an update.
- **Screen timeout:** after an always-on shot, a tap wakes the screen only briefly. So always-on shots go last in a run.
- **Editor:** tapping a box selects it, and tapping the selected box again moves to its next option. The first box is selected when the editor opens.
- **Settings take effect at the next minute tick.** The 12/24-hour switch is one, so wait about 62 s before shooting.
- **The clock** starts at `--time` (UTC) and keeps running.

**Emulator limits:**
- `zeus build` converts images to the watch's own compressed format, which the emulator can't decode. `tools/emu/prepare.py` swaps the original PNGs back in, for the emulator only.
- Test values (`set`) reach steps, calories, heart rate and battery through `@zos/sensor`, and every bound widget. Distance, PAI, stand, fat burning, blood oxygen and stress read 0 through `@zos/sensor` even when set (their bound widgets do show the values), and so do sleep, training, barometer, body temperature and compass, so check those on a real watch. For mock-ups, `DEMO_VALUES` in `design/config.py` (an override) shows given values instead of readings.
- The weather location is fixed (Beijing data: sunset 17:55). Weather values only update when they change.

The firmware log, including the face's `console.log` output, is in `tools/.emu/serial.log`. Watch state persists in `tools/.emu/flash.bin`.

### What the emulator confirmed (October 2026)

- **Packages:** a `.zab` holds one `.zpk` per screen and chip. Sextant's first test builds installed the 454×454 build, because `extract_zpk.py` took the first one. That made the face about 5% small and anchored top-left, which is why the time looked too small and the right-hand dividers sat too far in. `extract_zpk.py` now picks the package by device ID, defaulting to the Balance 3 (11141376).
- **Arc angles:** truncated to whole degrees (see above). This was the cause of the north marker crowding the tick to its right.
- **Text:** the firmware matches the line-box model in `text_box_for_ink_centre()` to within half a pixel, as long as boxes sit on whole pixels. Fractional `y` values were being rounded about 1–2px low. `FIRMWARE_TEXT_DY` in `lib/py/zfkit/fonts.py` is the calibration term, and it's 0.
- **Arcs:** `radius` is the centre of the stroke (`ARC_RADIUS_IS_CENTER = true`). The ticks match the offline renders exactly.
- **Weather:** face code can only read the forecast (per-day high, low and condition index, plus sun and moon times), at API level 1 and at 4.2. The 4.2 firmware names the call `getForecast()`, while the typings still say `getForecastWeather()`; `lib/js/sun.js` uses whichever exists. The current condition and temperature are only available to bound widgets, so the icon and the condition text are both `IMG_LEVEL` widgets bound to `WEATHER_CURRENT`.
- **API level 4.2** (migrated October 2026): the `@zos/*` modules are on the firmware with the same widget set and data types as API level 1 (`IMG_TIME`, `IMG_STATUS`, `IMG_LEVEL`, `TEXT_FONT`, `WATCHFACE_EDIT_GROUP`, `WIDGET_DELEGATE`). A sensor read without its permission in `app.json` throws "permission denied". `IMG` takes `angle` with `center_x` / `center_y` and the firmware rotates the image.
- **Edit mode** hides every normal widget and draws only `ONLY_EDIT` widgets and the edit groups, in creation order. So an edit-mode backdrop has to be created before the edit groups.
- **Custom edit types**, 12-hour mode, status icons, battery bands and automatic night mode all work as designed.

- **Always-on screen**, with the setting on and following the watch face, shows the outline time, date and battery.

Still to check on a real watch: **distance units** (`getDistanceUnit()`), °F for body temperature and the forecast (assumed to come in °C), and the readings of distance, PAI, stand, fat burning, blood oxygen, stress, sleep, training, barometer, body temperature and compass, which the emulator can't feed (see the emulator limits). If those read 0 on a watch, those metrics can go back to bound widgets in `lib/js/metrics.js`.

## Phone-side settings (not built)

A watch face can't receive anything from the phone. The Zepp app's Settings App reaches the watch only through a Side Service, and watch faces don't support one. The workaround, if a suite of faces ever justifies it:
- **Companion mini app:** a separate app with the Settings App and Side Service. It writes the choices to a file in its own storage on the watch.
- **The face:** reads that file with `hmFS.open(name, hmFS.O_RDONLY, { appid: <companion appId> })`. Example: [zeppos-autogui wf-app-comms](https://github.com/silver-zepp/zeppos-autogui/tree/master/other-autogui-examples/zeppos-3.0-wf-app-comms).
- **Drawbacks:** it's two installs, and the face can't update its own editor's selections, so the two would need a rule like "the most recent change wins".

## Sextant switches kept for later

- **White time:** `COLOR_TIME_STYLE = 'color_white'` in `faces/sextant/watchface/index.js`. The digits are already generated.
- **Barlow Condensed font** (previous font, fully aligned at time 111px, corner x 121.7):
  - Add the OFL Barlow Condensed files to `fonts/`.
  - Point `build_fonts()` at them.
  - Set `TIME_PX` to about 111 in `faces/sextant/design/config.py`.
  - Regenerate.
- **Faster-fade section tint** instead of black: colour near the rim, fading to black by about r=130 with a t^2.6 falloff. It needs per-metric tint images per section. This was prototyped in design renders but not built.

## Releasing

Each face is versioned and released on its own. The version is `version.name` in `faces/<face>/app.json`, and the release notes come from `faces/<face>/CHANGELOG.md` ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format).

To release a face:

1. Add the changes under `## [Unreleased]` in its `CHANGELOG.md` as you work.
2. When ready, rename that heading to `## [X.Y.Z] - YYYY-MM-DD` (leave a fresh empty `## [Unreleased]` above it).
3. Set the same `X.Y.Z` in `app.json` `version.name` and increase `version.code` by one.
4. Push to `main`.

CI (`.github/workflows/build.yml`) then:

- **On every push and PR:** runs `tools/release_plan.py`, which fails if any face's current version has no changelog section. Then it runs the harness and builds every face with Zeus.
- **On `main`, for each face whose `<face>-vX.Y.Z` tag doesn't exist yet:** creates the tag and a GitHub release titled e.g. "Sextant 1.1.0". The release notes are that version's changelog section plus install instructions, and `<face>-X.Y.Z.zpk` and `.zab` are attached. Anyone watching the repo for releases gets notified.
- **On every push to `main`:** builds a DEV test build of every face and redeploys the Pages site. The public part of the site always comes from the latest release of every face, so the main QR codes install released versions, never unreleased work on `main`.

Pushes that don't bump a version publish no release, only a new test build. A manual run (**Actions → Build and publish → Run workflow**) does the same.

### Test builds (before releasing)

Every push to `main` publishes a test build of each face on an unlisted page: **https://raetha.github.io/zepp-watch-faces/dev/**. It isn't linked from the main site, is marked `noindex`, and is blocked in `robots.txt`. Each run's summary also links to it.

- `tools/make_dev_variant.py` copies the face to `faces/<face>-dev/` (ignored by git). It gets its own `appId` (release ID + 1,000,000), the name "<Name> DEV" and the version `<X.Y.Z>-dev.<run number>`.
- Because the app ID differs, a test build installs **next to** the released face instead of replacing it. Pick it in the watch's face list to try it, then switch back.
- Its QR code (`zpkd1://raetha.github.io/zepp-watch-faces/dev/<face>/<face>.zpk`) never changes, so bookmark the page and rescan after each push. The Zepp app shows the build number, so you can confirm it picked up the new one. GitHub Pages can cache files for up to 10 minutes.
- The plan is to test on the watch, fix, push and repeat. Only when it all looks right do you finalize the changelog and bump `app.json`.

Each face's QR code (`faces/<face>/docs/install-qr.png`) encodes `zpkd1://raetha.github.io/zepp-watch-faces/<face>/<face>.zpk`, so it never needs regenerating. If the repo moves, run `npm run qr -- <face> <new zpkd1 url>`.

**Draft faces:** a face containing a `DRAFT` file is built and tested but never released. `npm run new-face` creates one; delete the file when the face is ready for its first release.

One-time repo setting: **Settings → Pages → Source: GitHub Actions**.

### App IDs

Each face has its own `appId`, outside the developer-preview range, so QR installs work without a Zepp developer account. Sextant is 8613207; `new_face.py` picks an unused random one. If you publish a face to a store, register it in the Zepp developer console and use the ID it assigns.

## Licensing (when adding code)

- **Reusable code** goes in `lib/` or `tools/`, which are MIT.
- **Face-specific artwork, layout and code** goes in `faces/<face>/`, which is CC BY-NC-SA 4.0.
- **Each face keeps its own `LICENSE`.** See the root `LICENSE`.

## Packaging for delivery

Deliver the whole repo tree as a zip, excluding build output:

```bash
zip -r zepp-watch-faces.zip . -x ".git/*" "node_modules/*" "*/dist/*" "tools/.build/*" "tools/.emu/*" "*/__pycache__/*" "site/*" "release/*" "out/*" "out-dev/*" "faces/*-dev/*"
```
