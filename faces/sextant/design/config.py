"""Design constants for the Sextant watch face.

Everything the asset generator and the watch-face layout share lives here, so
the PNG assets and the generated JS layout can never drift apart.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # faces/sextant
REPO = ROOT.parents[1]
FONT_DIR = REPO / "fonts"
# A face built from Sextant's generator (Twisted Sextant) sets SEXTANT_FACE_DIR to write
# its own assets and layout; its design/variant.json holds its overrides.
import os as _os0
OUT_FACE = Path(_os0.environ["SEXTANT_FACE_DIR"]) if _os0.environ.get("SEXTANT_FACE_DIR") else ROOT
ASSET_DIR = OUT_FACE / "assets" / "common.r"
LAYOUT_JS = OUT_FACE / "watchface" / "layout.generated.js"

# ----------------------------------------------------------------------------- screen
W = 480
C = W / 2

# ----------------------------------------------------------------------------- centre band
BAND_T, BAND_B = 160, 320                 # flat top / bottom edge of the band: exactly 1/3 of the height
BAND_IN = (BAND_T + 1, BAND_B - 1)         # inner edges of the 2px edge lines
MID = (BAND_T + BAND_B) / 2
BEND = (108, 372)                         # band edges are flat between these x, then flare
BAND_FLARE_SLOPE = math.tan(math.radians(10.85))   # flare solved so all six gauges are equal (19 ticks)

# separators inside the band (flared, same slope as the panel dividers)
SEP_X = (100, 380)                        # moved out from the band bend to give the time more room
SEP_INSET = 16                            # from band edge to separator end
SEP_FLARE_RUN = 30                        # vertical extent of each flared end

# ----------------------------------------------------------------------------- panel dividers
DIV_X = (186, 294)                        # vertical part of the dividers
ELBOW_Y = 110                             # complication layout reference (corner value tops sit here)
RIM_ANGLE = 248.5                         # top-left divider heads for this rim angle (PIL deg): centred
                                          #   in the gap between the gauges' end ticks (was 248.12)
DIV_START_GAP = 12                        # dividers stop this far from the band edge

# ----------------------------------------------------------------------------- outer ring
RING_R = 233                              # outer edge of the gauge ticks
TICK_MINOR, TICK_MAJOR = 6, 10            # tick lengths (inward from RING_R)
TICK_STEP = 2                             # degrees between ticks
TICK_MAJOR_EVERY = 10                     # a long tick every N degrees
SEG_GAP = 3.25                            # degrees of empty ring at each end of a gauge (was 6.5)
GAUGE_TRACK_R = 230                       # radius used to find where edges meet the ring

# ----------------------------------------------------------------------------- glances
GLANCE_SIZE = 22
GLANCES = ["disconnect", "dnd", "alarm", "lock"]

# ----------------------------------------------------------------------------- type
TIME_SIDE_GAP = 12                        # time size is solved so its widest value sits this far from each separator
# Layout: date left of the time, the time and condition text in the band, six
# complications (top-middle defaults to weather), and the status icons in pairs at the band
# in the top- and bottom-middle sections. Time and text are Roboto Condensed.
SECTION_GAP = 10                          # band edge -> status-icon pair
GLANCE_SECTIONS = (["alarm", "dnd"], ["disconnect", "lock"])   # top pair, bottom pair
GLANCE_PAIR_GAP = 14                      # gap between the two icons of a pair
RULE_FLAT = 64                            # rule between each pair and its metric: flat middle,
RULE_END_GAP = 6                          #   ends bent towards the rim (aimed at the divider
                                          #   elbows), stopping this far from the dividers
BRASS_FLOOR = 0.18                        # brass gradients (band edges, separators) keep at least
                                          #   this share of brass at their ends
# face options (Twisted Sextant sets these in its design/variant.json)
TURN_CORNERS = False                      # corner values run along their gauges, at the rim, with
                                          #   the icon inward (the top/bottom-middle layout turned)
DIAG_AT_GAUGE_MID = False                 # diagonal markers at the corner gauges' mid-points (43.5 deg)
                                          #   instead of 45.5, so they point at turned values
TIME_PX = None                            # (solved by the generator; tabular cells)
VALUE_PX = 40                             # complication values (Roboto Condensed Regular)
UNIT_PX = 20
DATE_SMALL_PX, DATE_DAY_PX = 32, 42
BATTERY_VALUE_PX = 40
DESC_PX = 22
ICON_PX = 32
ICON_GAP = 10                             # icon box <-> value box
VISIBLE_ICON_GAP = 13.5                   # the same gap measured on the drawings (icons sit ~3.5px inside their box)
LINE_W = 3                                # dividers, separators, band edges (2 was too faint on the watch)
WEATHER_ICON_PX = 38
BATTERY_ICON_PX = 34

# ----------------------------------------------------------------------------- colours
def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

METRICS = {
    # id: (title, colour, has_progress)
    "steps":    ("Steps",          "#3DDC84", True),
    "heart":    ("Heart rate",     "#FF4D5E", False),
    "distance": ("Distance",       "#3DA5FF", False),
    "calories": ("Calories",       "#FF8A3D", True),
    "floors":   ("Floors climbed", "#9D8CFF", True),
    "pai":      ("PAI",            "#2EE6C5", True),
    "stand":    ("Stand",          "#7FD1FF", True),
    "fatburn":  ("Fat burning",    "#FF7043", True),
    "spo2":     ("Blood oxygen",   "#FF6B8B", False),
    "stress":   ("Stress",         "#FFB13D", False),
    "uvi":      ("UV index",       "#D17BFF", False),
    "humidity": ("Humidity",       "#4FC3F7", False),
    "aqi":      ("Air quality",    "#A0D468", False),
    "sun":      ("Sunrise/sunset", "#FFC23D", False),
    "weather":  ("Weather",        "#8AB4F8", False),
    "resting":  ("Resting heart rate", "#FF8A95", False),
    "sleep":    ("Sleep",          "#8C9EFF", True),
    "sleepscore": ("Sleep score",  "#B39DFF", True),
    "bodytemp": ("Body temperature", "#FF9E80", False),
    "vo2max":   ("VO2 max",        "#4DD0E1", False),
    "trainload": ("Training load", "#FFD54F", False),
    "recovery": ("Recovery time",  "#81C784", False),
    "altitude": ("Altitude",       "#BCAAA4", False),
    "pressure": ("Air pressure",   "#90A4AE", False),
    "compass":  ("Compass",        "#E6C27A", False),
    "moon":     ("Moon phase",     "#E8E2C4", False),
    "forecast": ("Today's forecast", "#8AB4F8", False),
}
# small unit letters some metrics draw after their value (in the metric's colour)
UNIT_CHARS = {"distance": "kmi", "recovery": "h", "altitude": "mft", "pressure": "hPa", "compass": "NESW"}
DEFAULT_SLOTS = ["calories", "heart", "distance", "steps", "stand", "weather"]   # TL, TR, BL, BM, BR, TM
EDIT_METRICS = None                       # metrics the editable slots offer (None: all)
FIXED_SLOTS = {}                          # {slot index: metric} for slots that aren't editable
DEMO_VALUES = None                        # mock-ups only: {metric: {"text", "unit", "progress", "icon"}}
                                          #   shown instead of sensor readings the emulator can't feed

THEMES = {
    "color": dict(
        text=(244, 246, 248), muted=(150, 160, 172), accent=(214, 172, 96),
        desc=(255, 214, 120), divider=(52, 59, 68),
        band=((20, 34, 58), (8, 13, 24)), glow_lo=(20, 24, 30),
        time=((236, 205, 140), (196, 150, 72)),          # brass gradient (top -> bottom)
        aod_time=(214, 176, 112), aod_text=(180, 186, 194),
        dim_factor=0.30,
    ),
    "mono": dict(
        text=(244, 246, 248), muted=(150, 156, 164), accent=(206, 210, 216),
        desc=(220, 224, 230), divider=(58, 62, 68),
        band=((30, 32, 36), (10, 11, 13)), glow_lo=(22, 24, 26),
        time=((255, 255, 255), (196, 204, 214)),
        aod_time=(210, 214, 220), aod_text=(170, 174, 180),
        dim_factor=0.30, metric=(236, 238, 240), muted_icon=(120, 124, 130),
    ),
    "night": dict(
        text=(232, 44, 26), muted=(160, 30, 18), accent=(205, 38, 22),
        desc=(212, 40, 24), divider=(60, 10, 6),
        band=None, glow_lo=(16, 3, 2),                  # no band fill: pure black for night vision
        time=((240, 52, 30), (190, 34, 20)),
        aod_time=(190, 34, 20), aod_text=(150, 26, 16),
        dim_factor=0.28, metric=(222, 40, 24), muted_icon=(120, 22, 12),
    ),
}

BATTERY_COLORS = {"high": "#3DDC84", "mid": "#FFB03D", "low": "#FF4D5E"}

# weather condition index (Zepp OS) -> (icon kind, description)
WEATHER = [
    ("partly_day", "PARTLY CLOUDY"),      # 0
    ("shower", "SHOWERS"),                # 1
    ("snow_light", "SNOW FLURRIES"),      # 2
    ("sunny", "SUNNY"),                   # 3
    ("overcast", "OVERCAST"),             # 4
    ("rain_light", "LIGHT RAIN"),         # 5
    ("snow_light", "LIGHT SNOW"),         # 6
    ("rain", "RAIN"),                     # 7
    ("snow", "SNOW"),                     # 8
    ("snow_heavy", "HEAVY SNOW"),         # 9
    ("rain_heavy", "HEAVY RAIN"),         # 10
    ("dust", "DUST STORM"),               # 11
    ("sleet", "SLEET"),                   # 12
    ("fog", "FOG"),                       # 13
    ("fog", "HAZE"),                      # 14
    ("thunder", "T-STORMS"),              # 15
    ("snow_heavy", "SNOWSTORM"),          # 16
    ("dust", "DUST"),                     # 17
    ("rain_heavy", "SEVERE STORM"),       # 18
    ("hail", "HAIL"),                     # 19
    ("thunder", "T-STORMS & HAIL"),       # 20
    ("rain_heavy", "HEAVY STORM"),        # 21
    ("dust", "SAND"),                     # 22
    ("dust", "SANDSTORM"),                # 23
    ("rain_heavy", "RAINSTORM"),          # 24
    ("unknown", ""),                      # 25
    ("partly_night", "PARTLY CLOUDY"),    # 26
    ("shower", "SHOWERS"),                # 27
    ("clear_night", "CLEAR"),             # 28
]


# ----------------------------------------------------------------------------- overrides
# SEXTANT_OVERRIDES='{"VALUE_PX": 42}' python3 design/generate.py
# builds a variant without editing this file (used for side-by-side mock-ups).
import json as _json
import os as _os
for _k, _v in _json.loads(_os.environ.get("SEXTANT_OVERRIDES", "{}")).items():
    if _k not in globals():
        raise KeyError(f"unknown override {_k}")
    globals()[_k] = _v
# derived values follow any overridden band edges
BAND_IN = (BAND_T + 1, BAND_B - 1)
MID = (BAND_T + BAND_B) / 2

