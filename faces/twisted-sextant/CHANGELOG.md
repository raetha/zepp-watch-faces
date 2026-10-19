# Changelog: Twisted Sextant

All notable changes to the Twisted Sextant watch face. Format: Keep a Changelog; versions: SemVer.
The version here must match `version.name` in `app.json`; bumping it publishes a release.

## [Unreleased]

## [1.1.0] - 2026-10-19

### Changed
- The battery icon fills with the charge and empties a pixel at a time (about every 5%), on the always-on screen too. At 0% only the outline is left.

## [1.0.0] - 2026-10-18

### Added
- First release: Sextant with the corner complications turned to run along their gauges (values at the rim, icons inward, text kept the right way up), designed for the Amazfit Balance 3 and packaged for every round watch on Zepp OS API level 4.2 or later.
- The 22 metrics the face can read, in every editable slot: steps, distance, calories, stand, fat burning, PAI, heart rate, resting heart rate, blood oxygen, stress, body temperature, sleep, sleep score, VO2 max, training load, recovery time, today's forecast, altitude, air pressure, compass, sunrise and sunset, and moon phase.
- Weather fixed at the top. Defaults: calories, heart rate, distance, steps and stand.
- The diagonal compass markers sit at the middle of the corner gauges (43.5° rather than 45.5°), so each points at its turned value.
- Everything else matches Sextant: the time bar, status icons, tap-to-open complications, automatic night mode, the mono theme, the always-on screen and the editor languages.
