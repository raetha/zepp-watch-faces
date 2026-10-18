# Sextant design notes

The decisions behind the layout, so future changes keep the same logic. All numbers live in `design/config.py`, and the generator recomputes the derived positions from them.

## Principles

- Readable from arm's length. The time is large, the complication values are 40px, and there are no text labels. Each metric is identified by its own icon shape and colour.
- Everything is optically centred on glyph ink, not on font boxes.
- Things that look related share geometry: the band flare, the divider bends and the separator flares all use matching angles, and the six gauges are the same length.
- Battery-aware: black sections, a dim always-on screen with outline digits, and no seconds.

## Geometry

- **Centre band** (y 160–320, exactly a third of the screen height): flat between x 108 and 372, then flaring outward at 10.85°. That angle makes all six bezel gauges come out equal: 37.3° and 19 ticks each, with 3.25° of empty ring at each end. Early drafts had a 152px band at 13°, and a 6.5° gauge gap giving 30.9° and 16 ticks.
- **Band contents:**
  - The date stack is centred at x 50, and the battery icon and percentage at x 430, each midway between a separator and the screen edge.
    - Date: weekday and month at 32px and the day at 42px, with 10px between lines.
    - Battery: its drawing is short and wide, so it's spaced on the drawing itself, with the same visible gap as the complications (`VISIBLE_ICON_GAP`, 13.5px).
  - The time (Roboto Condensed, fixed-width digits, sized so it sits 12px from each separator: 121px) is centred between the separators at x 100 and 380.
  - The weather condition (22px caps) sits beneath the time. It only shows when some slot shows weather: without the temperature it's out of context. Time and condition are spread with three equal gaps in the band; with no condition the time centres by itself.
  - The band separators share the band edges' brass gradient. Both keep 18% brass at their ends (`BRASS_FLOOR`) instead of fading to the dim edge colour.
- **Status icons:** alarm and Do Not Disturb sit at the band in the top-middle section, Bluetooth and lock in the bottom-middle one (`GLANCE_SECTIONS`), `SECTION_GAP` (10px) from the band edge and 14px apart. The top- and bottom-middle values then sit the same distance from their ticks as the corner icons do. A rule separates each pair from its metric: a flat middle (`RULE_FLAT`, 64px) whose ends bend toward the rim, aimed at the divider elbows, stopping 6px from the dividers, in the divider colour.
  - Every icon always shows its off state (connected Bluetooth, dim outlines), with the active icon, drawn on a black disc, covering it. That way there's never a gap, and an alert still stands out.
- **Lines** (dividers, separators, band edges) are 3px wide. 2px was too faint on the watch.
- **Section dividers** rise vertically at x 186 and 294, then bend toward a rim angle of 248.5° (mirrored below), which centres them in the gap between the neighbouring gauges' end ticks (248.1° in 1.0.0 sat off-centre once the corner gauges gained a tick). The bend sits where that radius crosses the vertical run (y ≈ 103), so the outer run is radial, like the bezel ticks next to it. The band separators keep the original flare slope. The complications still use y 110 as their reference line.
- **Complications** use one box rule everywhere, so any metric can go in any slot:
  - Every icon is drawn centred in the same 32px box. Drawings differ in size (heart 22px tall, UV 30px).
  - Every value sits in the same box, from the digits' top to a comma's bottom, so "12,486" and "7" take the same space.
  - The icon box and the value box are 10px apart (`ICON_GAP`), above or below. Visible gaps vary a few pixels with the drawing and with commas, but rows stay aligned and mirror pairs match.
  - `tools/emu/audit.py` measures centring and gaps on an emulator screenshot.
- **Complication positions:**
  - Top corners: the top of the value's ink sits on the divider bend line, with the icon 10px above.
  - Bottom corners are exact mirrors.
  - Corner x positions (123.2 / 356.8) give a five-digit value such as "99,999" equal gaps to the divider and to the long ticks.
  - Bottom-middle: icon above value, the pair centred between the band and the ring.
  - Top-middle mirrors it, with the value above the icon, so both icons are nearest the band. It defaults to weather: the current-condition icon and the temperature.
- **Edit-mode tips** sit on a light brass panel. The firmware draws the tip text in a dark colour that a face can't change, so the panel has to be light for the text to be readable.

## Bezel

- Ticks every 2°, with a long tick every 10°.
- Six gauges:
  - The corner gauges start next to the top- or bottom-middle section and fill outward toward the band.
  - The bottom-middle gauge fills left to right, and the top-middle gauge right to left.
- **Whole-degree ticks:** the firmware truncates arc angles to whole degrees, and arcs under 1° don't draw. So each tick is exactly 1° wide (about 4px at the rim). Each tick covers the degree on the side away from the nearer centre-line point (12 or 6 o'clock), so the bezel is symmetric left/right and top/bottom: the ticks either side of both markers sit 2.5° from them. A single whole-degree grid can't be symmetric with 2° spacing and 1° ticks, which is why the halves differ. They only meet at the band, where there are no ticks. Early builds asked for `c ± 0.32°`, and every tick was truncated the same way. That shifted them 0.5° anticlockwise, so the tick right of north crowded the marker.
- **Corner gauges** have one more tick at their divider end, so their gap to the divider (about 2.1°) is close to the middle gauges' (2.9°) instead of 4.1°.
- **Markers:** triangles at north, south and the four diagonals (45.5° and mirrored, with the ticks either side removed). Each is brass until its gauge's fill passes it, then takes the gauge's colour. They're images, because a triangle built from whole-degree arcs is blocky.

## Colour

- **Colour theme:** navy band, brass accents (214,172,96), brass time gradient. Metric colours: steps green, heart red, distance blue, calories orange, floors violet, and so on.
- **Night theme:** everything deep red on pure black, with no band fill (only its red edge lines) (text contrast ≈5.3:1, the practical limit for pure red).
- **Mono theme:** white and greys on black.

## Twisted Sextant

Twisted Sextant (`faces/twisted-sextant/`) is this design with three face options set in its `design/variant.json`:
- `TURN_CORNERS`: each corner takes the top- or bottom-middle layout turned 43.5° about the centre (to its gauge's mid-point), with the value at the rim (the same gap to the ticks) and the icon inward, and text kept the right way up. Text widgets can't rotate, so the face lays each value out from one image per character (0–9 , . - : % / ° and the units' letters, per theme), and the firmware turns each image (`IMG` `angle`); the icons turn the same way. Bound metrics (floors, weather, UV, humidity, air quality) can't be turned, because the face never gets their numbers, so Twisted Sextant doesn't offer them in its slots (`EDIT_METRICS`).
- `DIAG_AT_GAUGE_MID`: the diagonal markers move to 43.5°, the corner gauges' mid-points, so each points at its turned value.
- Weather is fixed at the top (`FIXED_SLOTS`), and the defaults are its own (`DEFAULT_SLOTS`).

## Tried and dropped

Both designs were locked on 2026-10-18 and the switches for the alternatives were removed. They're in the git history before that date if one is ever wanted again:
- Status icons in a row above the time (1.0.0), beside the condition text, under or over the band, or in the band's four corners around the time.
- Rules between the status icons and their metrics: short, long, flared towards the band, and brass-gradient versions.
- Markers: north and south only, dim until passed (1.0.0); fixed brass at two or eight points.
- Grey separators (1.0.0), the original brass fade to near-black at the ends, no extra corner tick, the 1.0.0 divider bend and angle (248.1°).
- Roboto Regular for the time, a larger weekday and month, white time digits, and value boxes without the comma's depth.
- Never built: Barlow Condensed as the font, and a colour tint fading into each section.
- The pre-1.0 layout (date top-middle, weather in the band, five complications, a brass compass scale) is described in the 1.0.0 history only.
