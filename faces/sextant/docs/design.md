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
  - The time (Roboto Condensed, fixed-width digits, sized so it sits 12px from each separator: 121px) is centred between the separators at x 100 and 380. `TIME_FONT_STYLE = "regular"` gives the original Roboto at 106px.
  - The weather condition (22px caps) sits beneath the time. It only shows when some slot shows weather: without the temperature it's out of context. Time and condition are spread with three equal gaps in the band; with no condition the time centres by itself.
  - The band separators share the band edges' brass gradient (`SEPARATOR_BRASS`). Both keep 18% brass at their ends (`BRASS_FLOOR`) instead of fading to the dim edge colour.
- **Status icons** have three modes, set by `GLANCE_MODE` in `config.py`:
  - `"sections"` (default): alarm and Do Not Disturb sit at the band in the top-middle section, Bluetooth and lock in the bottom-middle one (`GLANCE_SECTIONS`), `SECTION_GAP` (10px) from the band edge. The top- and bottom-middle values then sit the same distance from their ticks as the corner icons do. A rule separates each pair from its metric (`SECTION_RULES`): a flat middle (`RULE_FLAT`, 64px) whose ends bend toward the rim, aimed at the divider elbows, stopping 6px from the dividers (`RULE_STYLE = "flare_out"`; also `short`, `long`, `flare_in`, and `_brass` variants).
  - `"row"` (1.0.0): a centred row above the time with 14px between icons. Row, time and condition are stacked with four equal gaps (about 8.5px).
  - `"split"`: Bluetooth and lock sit left of the condition text, Do Not Disturb and alarm right of it, in the same row. Each pair is centred between the separator and the widest condition name. Time and condition then use three equal gaps (about 19px).
  - Active status icons sit on a disc of the band colour at their position, so the disc doesn't show.
- **Lines** (dividers, separators, band edges) are 3px wide. 2px was too faint on the watch.
- **Section dividers** rise vertically at x 186 and 294, then bend toward a rim angle of 248.5° (mirrored below), which centres them in the gap between the neighbouring gauges' end ticks (248.1° in 1.0.0 sat off-centre once the corner gauges gained a tick). The bend sits where that radius crosses the vertical run (y ≈ 103), so the outer run is radial, like the bezel ticks next to it. `DIVIDER_RADIAL = False` puts the bend back at y 110. The band separators keep the original flare slope. The complications still use y 110 as their reference line.
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
- **Status icons:** four fixed slots on an arc of radius 205. Along the arc, the gaps from each divider's stroke to the first icon and between neighbouring icons are all equal. Every slot always shows its off state (connected Bluetooth, dim outlines), with the active icon, drawn on a black disc, covering it. That way there's never a gap, and an alert still stands out.
- **Edit-mode tips** sit on a light brass panel. The firmware draws the tip text in a dark colour that a face can't change, so the panel has to be light for the text to be readable.

## Bezel

- Ticks every 2°, with a long tick every 10°.
- Six gauges:
  - The corner gauges start next to the top- or bottom-middle section and fill outward toward the band.
  - The bottom-middle gauge fills left to right, and the top-middle gauge right to left.
- **Whole-degree ticks:** the firmware truncates arc angles to whole degrees, and arcs under 1° don't draw. So each tick is exactly 1° wide (about 4px at the rim). Each tick covers the degree on the side away from the nearer centre-line point (12 or 6 o'clock), so the bezel is symmetric left/right and top/bottom: the ticks either side of both markers sit 2.5° from them. A single whole-degree grid can't be symmetric with 2° spacing and 1° ticks, which is why the halves differ. They only meet at the band, where there are no ticks. Early builds asked for `c ± 0.32°`, and every tick was truncated the same way. That shifted them 0.5° anticlockwise, so the tick right of north crowded the marker.
- **Corner gauges** have one more tick at their divider end (`CORNER_EXTRA_TICK`), so their gap to the divider (about 2.1°) is close to the middle gauges' (2.9°) instead of 4.1°.
- **Markers** (`MARKERS = "brass6"`): triangles at north, south and the four diagonals (45.5° and mirrored, with the ticks either side removed). Each is brass until its gauge's fill passes it, then takes the gauge's colour. They're images, because a triangle built from whole-degree arcs is blocky. `"progress"` (1.0.0) has only north and south, dim until passed; `"brass2"` and `"brass8"` are fixed brass.
- The earlier pre-release layout is kept on the git branch `archive/previous-layout`. It had the date top-middle, weather on the left of the band, five complications and a brass compass scale with a north marker over the date.

## Colour

- **Colour theme:** navy band, brass accents (214,172,96), brass time gradient. Metric colours: steps green, heart red, distance blue, calories orange, floors violet, and so on.
- **Night theme:** everything deep red on pure black, with no band fill (only its red edge lines) (text contrast ≈5.3:1, the practical limit for pure red).
- **Mono theme:** white and greys on black.

## Options kept for later

- White time instead of brass (`COLOR_TIME_STYLE`).
- Barlow Condensed as the font (fully aligned previously).
- A faster-fade colour tint in each section instead of black.

See the repository's `docs/development.md` for how to switch to any of these.

## To review on the watch

- **Status icons beside the condition text** (`GLANCE_MODE = "split"`): Bluetooth and lock on the left, Do Not Disturb and alarm on the right, with the time and condition evenly spaced (about 19px gaps, roomier than the 8.5px of row mode). Compare it with the row above the time once 1.0.0 is on the watch.
- **Bezel balance:** the dividers moved to 248.5° to centre them between the gauges' end ticks. If the gaps still look uneven, adjust `RIM_ANGLE` (the ticks stay put for small changes) or `SEG_GAP`.
- **Brass ends** (`BRASS_FLOOR`, 0.18): check on the wrist whether the band edges and separators need it at all now the lines are 3px. 0 is the original fade to near-black; 0.35 was also tried.
- **Status icon row** (`GLANCE_MODE = "row"`, the 1.0.0 layout), if the sections layout doesn't hold up on the wrist.
- **Previous layout** (branch `archive/previous-layout`), in case the new one doesn't hold up on the wrist.
- **Status icons in the band's corners** (tried 2026-10-17 and liked; `SECTION_LAYOUT = "corners"`). The recipe:
  - The band holds only the time: condensed, 121px, centred, about 31px from each band edge.
  - The four status icons sit at full size (22px) in the band's corners around the time. Bluetooth is top left, Do Not Disturb top right, alarm bottom left and lock bottom right.
  - Each icon is the same distance from the band edge and from the separator's flared end. That distance (about 5.75px) is solved as the largest that keeps `CORNER_TIME_CLEAR` (3px) from the time's ink.
  - The active icons sit on discs of the band colour at their position.
  - The weather moves to the bottom-middle section. Its icon box top is level with the bottom corners' value tops, the temperature sits below it, and the condition text is centred between the temperature and the bottom marker.
  - Steps is top-middle and calories top-left. The date is 32/42/32px, as now. The band was the 152px one then; with the 160px band the corner gap grows a little.
  - Override: `{"SECTION_LAYOUT": "corners", "DEFAULT_SLOTS": ["calories","heart","distance","weather","floors","steps"]}` (plus the 152px band to reproduce it exactly: `BAND_T` 164, `BAND_B` 316, and a 13° flare).
