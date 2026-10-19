# Changelog: Sextant

All notable changes to the Sextant watch face. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/). The version here must match
`version.name` in `app.json`; bumping it is what publishes a release.

## [Unreleased]

### Changed
- The battery icon fills with the charge and empties a pixel at a time (about every 5%), on the always-on screen too. At 0% only the outline is left.

## [1.0.0] - 2026-10-18

### Added
- First release, designed for the Amazfit Balance 3 (480×480 round) and packaged for every round watch on Zepp OS API level 4.2 or later (480×480 and 466×466).
- A large, fixed-width brass time (Roboto Condensed) centred on a navy bar that's a third of the screen tall, with the date on the left and the battery on the right. The battery icon turns orange at 40% and red at 20%. When a complication shows weather, the current condition's name sits under the time.
- Six editable complications, each with a compass-tick gauge on the bezel. Defaults: calories, heart rate, distance, steps, stand and the weather (top centre).
- 27 choices, grouped in the editor: activity (steps, distance in km or mi, calories, floors, stand, fat burning, PAI), body (heart rate, resting heart rate, blood oxygen, stress, body temperature, sleep, sleep score), training (VO2 max, training load, recovery time), outdoors (weather, today's forecast, UV, humidity, air quality, altitude, air pressure, compass heading with its cardinal point) and sky (next sunrise or sunset, moon phase).
- Goal-based metrics (steps, calories, stand, fat burning, sleep and more) light their gauge's ticks. Compass markers at north, south and the four diagonals stay brass until a gauge's progress passes them, then take its colour.
- Status icons for alarm and Do Not Disturb above the bar, and Bluetooth and screen lock below it. Each always shows something: a dim outline when off, lit when on, and Bluetooth red-slashed when disconnected.
- Tap a complication to open its app: heart rate, weather, sleep, PAI, stress, the activity summary, training status, altimeter, compass, thermometer or sun and moon.
- Automatic night mode: deep red on pure black between sunset and sunrise, each red as dim as it can be while staying readable. It can be switched off in edit mode.
- Mono theme for colour-blind users, selectable in edit mode.
- A low-power always-on screen: 2px outline digits where the time sits on the normal screen, plus the date and battery.
- Editor titles in English, Simplified Chinese and Traditional Chinese.
- Install by QR code from the Zepp app's developer mode.
