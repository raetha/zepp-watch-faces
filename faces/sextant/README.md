# Sextant

A nautical, data-rich watch face for the **Amazfit Balance 3** (480×480 round, Zepp OS).

A navy and brass time bar runs across the middle. Five complications sit around it, and each section's progress shows as compass-style ticks on the bezel. The time stays readable at a glance, and the data stays readable without squinting.

<p align="center"><img src="screenshots/day.png" width="360" alt="Sextant, default look"></p>

## Install

<img src="docs/install-qr.png" width="200" align="right" alt="Install QR code">

1. In the **Zepp app**, turn on Developer Mode: **Profile → Settings → About**, then tap the Zepp logo 7 times.
2. Go to **Profile → your watch → Developer Mode** and tap the **scan** icon (top right).
3. Scan this QR code and confirm.

The QR code always installs the latest release (see the [changelog](CHANGELOG.md)). You can also download `sextant.zpk` from the [install page](https://raetha.github.io/zepp-watch-faces/) or from the [releases](https://github.com/raetha/zepp-watch-faces/releases).

<br clear="right">

## Modes and styles

| Day (default) | Night (automatic, sunset → sunrise) | Mono theme |
| :---: | :---: | :---: |
| <img src="screenshots/day.png" width="250"> | <img src="screenshots/night.png" width="250"> | <img src="screenshots/mono.png" width="250"> |
| **Always-on** | **Other complications** | **Edit mode** |
| <img src="screenshots/day_aod.png" width="250"> | <img src="screenshots/alt.png" width="250"> | <img src="screenshots/day_edit.png" width="250"> |

All screenshots are taken on the real Zepp OS firmware (Amazfit Balance 2 emulator image). The emulator's distance sensor always reads 0.

## Features

- **Time:** a large, fixed-width time that never shifts sideways. Follows your 12/24-hour setting (no AM/PM by design). No seconds.
- **Weather:** the current condition's icon and temperature at the top (a complication, so it can move or be swapped), with the condition's name under the time (shown whenever a complication shows weather).
- **Battery:** icon and percentage on the right. The icon turns orange at 40% and red at 20%.
- **Date:** weekday, day and month on the left of the time bar.
- **Status icons** above the time: Bluetooth, Do Not Disturb, alarm and screen lock. Each slot always shows something: a blue Bluetooth icon while connected (a red slashed one when disconnected), and a dim outline for the others that lights up in colour when that mode is on.
- **Six editable complications.** Long-press the face → **Edit**, then tap any section. Choices:
  - steps, heart rate, distance (km or mi, following your watch setting), calories, floors climbed
  - PAI, stand, fat-burning minutes, blood oxygen, stress
  - UV index, humidity, air quality, next sunrise or sunset, weather
- **Progress ticks:** goal-based metrics light up their section's ticks. The top and bottom gauges have a marker at the halfway point that lights up too.
- **Night mode:** everything switches to deep red on pure black between sunset and sunrise, using your weather location's sun times. Turn it off in Edit mode (tap the time).
- **Mono theme:** an all-white-on-black version, friendly to colour-blind users. Pick it in Edit mode (tap the date).
- **Always-on display:** outline digits with the date and battery on black, to save battery.

Every metric has its own icon shape, so colour is never the only cue. Day-mode text meets WCAG contrast guidelines.

## Development

Sextant lives in the [zepp-watch-faces](../../README.md) collection. For the shared workflow, see [`docs/development.md`](../../docs/development.md); for this face's design rationale, see [`docs/design.md`](docs/design.md).

```bash
python3 faces/sextant/design/generate.py   # regenerate this face's images + layout
node tools/harness/run_scenarios.mjs sextant
```

## License

This face (everything in `faces/sextant/`) is licensed under [CC BY-NC-SA 4.0](LICENSE): share and remix it non-commercially with credit, but don't sell it. The name "Sextant" isn't licensed for reuse. The shared tooling it builds on is MIT, and the fonts are under the SIL Open Font License. See the repository [LICENSE](../../LICENSE).
