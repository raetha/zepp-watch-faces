# Changelog: Sextant

All notable changes to the Sextant watch face. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/). The version here must match
`version.name` in `app.json`; bumping it is what publishes a release.

## [Unreleased]

### Changed
- The time bar is exactly a third of the screen height, and the time uses Roboto Condensed at 121px (was Roboto at 106px).
- Weekday and month are bigger (32px, was 21px), so they're easier to read.
- Dividers, separators and band edges are 1px wider (3px), because 2px was too faint on the watch.
- Steps moves to the bottom centre, calories to the top left, and stand takes the bottom right (was floors).
- The weather condition under the time only shows when a complication shows weather.
- The status icons move out of the time bar: alarm and Do Not Disturb at the bottom of the top-centre section, Bluetooth and lock at the top of the bottom-centre section, each pair set off from its metric by a flared rule. The time and the weather condition now spread evenly in the bar, and the time centres by itself when no complication shows weather.
- Compass markers at north, south and the four diagonals. They stay brass until their gauge's progress passes them, then take the gauge's colour.
- The corner gauges gain a tick, and the section dividers are centred in the gaps between gauges.
- The bar's separators take the brass gradient of its edges, and both keep a little brass at their ends.

- Twelve more complications: resting heart rate, sleep (with progress towards your sleep goal), sleep score, body temperature, VO2 max, training load, recovery time, altitude, air pressure, compass heading (degrees and the cardinal point, like 312° NW), moon phase and today's forecast (high/low and condition). The editor list is grouped: activity, body, training, outdoors, then sun and moon.
- Tap a complication to open the matching app: heart rate, weather, sleep, PAI, stress, the activity summary, training status, altimeter, compass, thermometer or sun and moon. A long press or a swipe that starts on a complication doesn't open anything.
- Built on Zepp OS API level 4.2 (was 1.0). Stand, fat burning, blood oxygen and stress are now read directly, so stand and fat burning light their gauges towards their daily goals.

- The always-on time stays where it is on the normal screen, with the weather condition under it, so nothing jumps when the screen dims. Its outline digits are 2px (were 1.4px).
- Night mode's dimmer reds (month, condition text, units, always-on text) are a little brighter, so each meets readability guidelines.
- Units (km, hPa, ...) are 22px, Zepp's minimum text size (were 20px).
- Editor titles in Simplified and Traditional Chinese.

### Fixed
- Less work on the watch: values are only redrawn when they change, the always-on screen ignores sensor updates, and sleep data is refreshed at most every 10 minutes.
- Icons are centred in their boxes, and the battery icon has the same gap to its percentage as the complications.
- A value with a comma (like 12,486) above its icon no longer crowds the icon.

## [1.0.0] - 2026-10-16

### Added
- First release for the Amazfit Balance 3 (480×480 round).
- A large brass time on a navy band, with the current weather condition under it and a row of status icons above it (Bluetooth, Do Not Disturb, alarm, screen lock). Each icon always shows something: a dim outline when off, lit when on, and Bluetooth red-slashed when disconnected.
- The date on the left of the band and the battery on the right. The battery icon turns orange at 40% and red at 20%.
- Six editable complications, each with a tick gauge on the bezel. The top-middle one defaults to weather (current-condition icon and temperature).
  - Choices: steps, heart rate, distance (km or mi), calories, floors, PAI, stand, fat burning, blood oxygen, stress, UV index, humidity, air quality, next sunrise or sunset, and weather.
  - Goal-based metrics light their gauge's ticks. The top and bottom gauges have a marker at the halfway point that lights up too.
- Automatic night mode, deep red on pure black between sunset and sunrise. It can be switched off in edit mode.
- Mono theme for colour-blind users, selectable in edit mode.
- Always-on display with outline digits, date and battery.
- Install by QR code from the Zepp app's developer mode.
