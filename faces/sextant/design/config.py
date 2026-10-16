"""Design constants for the Sextant watch face.

Everything the asset generator and the watch-face layout share lives here, so
the PNG assets and the generated JS layout can never drift apart.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # faces/sextant
REPO = ROOT.parents[1]
FONT_DIR = REPO / "fonts"
ASSET_DIR = ROOT / "assets" / "common.r"
LAYOUT_JS = ROOT / "watchface" / "layout.generated.js"

# ----------------------------------------------------------------------------- screen
W = 480
C = W / 2

# ----------------------------------------------------------------------------- centre band
BAND_T, BAND_B = 164, 316                 # flat top / bottom edge of the band
BAND_IN = (BAND_T + 1, BAND_B - 1)         # inner edges of the 2px edge lines
MID = (BAND_T + BAND_B) / 2
BEND = (108, 372)                         # band edges are flat between these x, then flare
BAND_FLARE_SLOPE = math.tan(math.radians(13.0))

# separators inside the band (flared, same slope as the panel dividers)
SEP_X = (100, 380)                        # moved out from the band bend to give the time more room
SEP_INSET = 16                            # from band edge to separator end
SEP_FLARE_RUN = 30                        # vertical extent of each flared end

# ----------------------------------------------------------------------------- panel dividers
DIV_X = (186, 294)                        # vertical part of the dividers
ELBOW_Y = 110                             # complication layout reference (value tops sit here)
DIVIDER_RADIAL = True  # bend the dividers where their outer run points at the centre,
                                          # so it is parallel to the bezel ticks (else bend at ELBOW_Y)
RIM_ANGLE = 248.12                        # top-left divider heads for this rim angle (PIL deg)
DIV_START_GAP = 12                        # dividers stop this far from the band edge

# ----------------------------------------------------------------------------- outer ring
RING_R = 233                              # outer edge of the gauge ticks
TICK_MINOR, TICK_MAJOR = 6, 10            # tick lengths (inward from RING_R)
TICK_STEP = 2                             # degrees between ticks
TICK_MAJOR_EVERY = 10                     # a long tick every N degrees
TICK_WIDTH = 2.6
SEG_GAP = 3.25                            # degrees of empty ring at each end of a gauge (was 6.5)
GAUGE_TRACK_R = 230                       # radius used to find where edges meet the ring

# ----------------------------------------------------------------------------- glances
GLANCE_R = 205                            # icons ride this arc, evenly spaced between the two dividers
GLANCE_SIZE = 22
GLANCES = ["disconnect", "dnd", "alarm", "lock"]

# ----------------------------------------------------------------------------- type
TIME_SIDE_GAP = 12                        # time size is solved so its widest value sits this far from each separator
# Layout: date left of the time, six complications (top-middle defaults to weather).
# The earlier pre-release layout (date top-middle, weather in the band, compass scale)
# is kept on the git branch archive/previous-layout.
GLANCE_MODE = "row"                       # "row": status icons in a row above the time
                                          # "split": two each side of the condition text
GLANCE_ROW_GAP = 14                       # row mode: gap between icons
GLANCE_SPLIT = (["disconnect", "lock"], ["dnd", "alarm"])   # split mode: left pair, right pair
GLANCE_PAIR_GAP = 8                       # split mode: gap between the two icons of a pair
                      # time centred in the band; condition text centred below it
TIME_PX = None                            # (solved by the generator; Roboto Regular, normal width, tabular cells)
VALUE_PX = 40                             # complication values (Roboto Condensed Regular)
UNIT_PX = 20
DATE_SMALL_PX, DATE_DAY_PX = 21, 42
SIDE_VALUE_PX = 42                        # temperature
BATTERY_VALUE_PX = 40
DESC_PX = 22
ICON_PX = 32
ICON_GAP = 10
WEATHER_ICON_PX = 38
BATTERY_ICON_PX = 34
SIDE_BLOCK_GAP = 12

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
}
DEFAULT_SLOTS = ["steps", "heart", "distance", "calories", "floors", "weather"]   # TL, TR, BL, BM, BR, TM

THEMES = {
    "color": dict(
        text=(244, 246, 248), muted=(150, 160, 172), accent=(214, 172, 96),
        desc=(255, 214, 120), divider=(52, 59, 68),
        band=((20, 34, 58), (8, 13, 24)), glow_lo=(20, 24, 30),
        time=((236, 205, 140), (196, 150, 72)),          # brass gradient (top -> bottom)
        time_alt_white=((255, 255, 255), (196, 204, 214)),
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
