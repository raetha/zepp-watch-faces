"""Generate every watch-face asset plus watchface/layout.generated.js.

Run:  python3 faces/sextant/design/generate.py   (or `npm run assets`)
"""
import json
import math
import shutil
import numpy as np
from PIL import Image, ImageDraw

from . import config as K
from . import geometry as G
from zfkit import fonts as F
from zfkit.icons import (METRIC_SVG, BATTERY_SVG, GLANCE_SVG, GLANCE_OFF_SVG, weather_svg, svg_to_image, retint)

S = 3                      # supersampling for vector drawing
OUT = K.ASSET_DIR
THEME_NAMES = ["color", "mono", "night"]


def P(v):
    return int(round(v * S))


def lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def save(img, rel):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return rel


def down(img):
    return img.resize((img.width // S, img.height // S), Image.LANCZOS)


def hexint(rgb):
    return int("%02x%02x%02x" % tuple(rgb), 16)


# ============================================================================= backgrounds
def draw_band(img, theme):
    t = K.THEMES[theme]
    if t["band"] is not None:
        _band_fill(img, t)
    d = ImageDraw.Draw(img)
    for fn in (G.band_top_y, G.band_bot_y):
        xs = np.linspace(-10, K.W + 10, 1200)
        for xa, xb in zip(xs[:-1], xs[1:]):
            f = 1 - abs((xa + xb) / 2 / K.W - 0.5) * 2
            col = lerp(t["glow_lo"], t["accent"], max(0, f) ** 1.8)
            d.line([P(xa), P(fn(xa)), P(xb), P(fn(xb))], fill=col, width=P(2))


def _band_fill(img, t):
    lo, hi = t["band"]
    # horizontal gradient with a little noise so dark themes do not band
    f = (np.abs(np.arange(img.width) / img.width - 0.5) * 2) ** 1.4
    col = np.array(lo, float)[None, :] * (1 - f[:, None]) + np.array(hi, float)[None, :] * f[:, None]
    rng = np.random.default_rng(7)
    arr = col[None, :, :] + rng.uniform(-1.6, 1.6, (img.height, img.width, 3))
    arr = np.clip(np.round(arr), 0, 255).astype(np.uint8)
    grad = Image.fromarray(np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)]), "RGBA")
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).polygon(G.band_polygon(S), fill=255)
    img.paste(grad, (0, 0), m)


def draw_dividers(d, theme):
    col = K.THEMES[theme]["divider"]
    for top in (True, False):
        for side in "LR":
            pts = G.divider_points(side, top)
            y0 = K.BAND_T - K.DIV_START_GAP if top else K.BAND_B + K.DIV_START_GAP
            pts = [(pts[0][0], y0)] + pts[1:]
            d.line([(P(x), P(y)) for x, y in pts], fill=col, width=P(2), joint="curve")


def draw_separators(d, col):
    for i in (0, 1):
        d.line([(P(x), P(y)) for x, y in G.separator_points(i)], fill=col, width=P(2), joint="curve")


def tick_line(d, deg, col, length, r_out=K.RING_R, width=K.TICK_WIDTH):
    ca, sa = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    d.line([P(K.C + r_out * ca), P(K.C + r_out * sa),
            P(K.C + (r_out - length) * ca), P(K.C + (r_out - length) * sa)], fill=col, width=P(width))




MARKER_TIP_R, MARKER_BASE_R, MARKER_HALF_W, MARKER_BOX = K.RING_R - 13, K.RING_R + 1, 5.0, 16


def make_markers():
    """Triangle markers on the centre line of the top- and bottom-middle gauges (their 50%
    point), lit and dim in every metric colour, so code can switch them like a tick.
    They're images because the firmware draws arcs only in whole degrees."""
    h = (MARKER_BASE_R - MARKER_TIP_R) * S
    c = MARKER_BOX * S / 2
    for theme in THEME_NAMES:
        t = K.THEMES[theme]
        for metric in K.METRICS:
            rgb = metric_rgb(theme, metric)
            for state, col in (("lit", rgb), ("dim", lerp((0, 0, 0), rgb, t["dim_factor"]))):
                for name, sign in (("top", 1), ("bottom", -1)):     # tip towards the centre
                    img = Image.new("RGBA", (MARKER_BOX * S, MARKER_BOX * S), (0, 0, 0, 0))
                    ImageDraw.Draw(img).polygon([(c, c + sign * h / 2), (c - P(MARKER_HALF_W), c - sign * h / 2),
                                                 (c + P(MARKER_HALF_W), c - sign * h / 2)], fill=col + (255,))
                    save(down(img), f"marker/{theme}/{name}_{metric}_{state}.png")
    cy = K.C - (MARKER_TIP_R + MARKER_BASE_R) / 2
    x = round(K.C - MARKER_BOX / 2)
    return dict(top=dict(x=x, y=round(cy - MARKER_BOX / 2)), bottom=dict(x=x, y=round(K.W - cy - MARKER_BOX / 2)))


def round_crop(img):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, img.width - 1, img.height - 1], fill=255)
    out = Image.new("RGBA", img.size, (0, 0, 0, 255))
    out.paste(img, (0, 0), m)
    return out


def make_backgrounds():
    paths = {}
    for theme in THEME_NAMES:
        img = Image.new("RGBA", (K.W * S, K.W * S), (0, 0, 0, 255))
        d = ImageDraw.Draw(img)
        draw_dividers(d, theme)
        draw_band(img, theme)
        d = ImageDraw.Draw(img)
        draw_separators(d, K.THEMES[theme]["divider"])
        paths[theme] = save(down(round_crop(img)).convert("RGB"), f"bg/{theme}.png")
        # always-on background: separators only, very dim
        aod = Image.new("RGBA", (K.W * S, K.W * S), (0, 0, 0, 0))
        dim = lerp(K.THEMES[theme]["divider"], (0, 0, 0), 0.25)
        draw_separators(ImageDraw.Draw(aod), dim)
        paths[f"aod_{theme}"] = save(down(aod), f"aod/bg_{theme}.png")
    return paths


# ============================================================================= time digits
def TF():
    """The time-digit font for this build."""
    return F.TEXT_FONT if K.TIME_FONT_STYLE == "condensed" else F.TIME_FONT


def solve_time_px():
    """Largest time size whose widest value keeps TIME_SIDE_GAP to each separator (and, when
    the time is alone in the band, TIME_MIN_VGAP to the band edges)."""
    def fits_height(px):
        if not K.SECTION_LAYOUT:
            return True
        ex = [F.ink_extent(TF(), px, ch) for ch in "0123456789"]
        ink = max(e[3] for e in ex) - min(e[1] for e in ex)
        return ink <= (K.BAND_IN[1] - K.BAND_IN[0]) - 2 * K.TIME_MIN_VGAP

    def gap(px):
        f = F.pil_font(str(TF()), px, S)
        adv = f.getlength("0", features=["tnum"]) / S
        ex = [F.ink_extent(TF(), px, ch) for ch in "0123456789"]
        colon = round(px * 22 / 124, 1)
        worst = 4 * adv + colon - min(e[0] for e in ex) - (adv - max(e[2] for e in ex))
        return (K.SEP_X[1] - 1 - (K.SEP_X[0] + 1) - worst) / 2
    lo, hi = 60, 200
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if gap(mid) >= K.TIME_SIDE_GAP and fits_height(mid) else (lo, mid)
    return lo


def time_metrics():
    f = F.pil_font(str(TF()), K.TIME_PX, S)
    adv = f.getlength("0", features=["tnum"]) / S
    tops, bots, lefts, rights = [], [], [], []
    for ch in "0123456789":
        x0, t, x1, b = F.ink_extent(TF(), K.TIME_PX, ch)
        tops.append(t); bots.append(b); lefts.append(x0); rights.append(x1)
    return dict(adv=adv, top=min(tops), bot=max(bots), lsb_min=min(lefts), right_max=max(rights),
                colon_w=round(K.TIME_PX * 22 / 124, 1))


def make_time_digits():
    tm = time_metrics()
    pad = 3
    cell_w = int(math.ceil(tm["adv"]))
    cell_h = int(math.ceil(tm["bot"] - tm["top"])) + 2 * pad
    base_y = -tm["top"] + pad                       # baseline inside the cell
    f = F.pil_font(str(TF()), K.TIME_PX, S)
    styles = {
        "color": K.THEMES["color"]["time"],
        "color_white": K.THEMES["color"]["time_alt_white"],
        "mono": K.THEMES["mono"]["time"],
        "night": K.THEMES["night"]["time"],
    }
    colon_w = int(math.ceil(tm["colon_w"]))
    ink_mid = (tm["top"] + tm["bot"]) / 2 - tm["top"] + pad   # ink centre inside cell
    for name, (c_top, c_bot) in styles.items():
        for ch in "0123456789":
            m = Image.new("L", (cell_w * S, cell_h * S), 0)
            ImageDraw.Draw(m).text((0, base_y * S), ch, font=f, fill=255, anchor="ls", features=["tnum"])
            grad = Image.new("RGB", m.size)
            gd = ImageDraw.Draw(grad)
            for y in range(m.height):
                tt = np.clip((y / S - pad) / (cell_h - 2 * pad), 0, 1)
                gd.line([(0, y), (m.width, y)], fill=lerp(c_top, c_bot, tt))
            img = grad.convert("RGBA"); img.putalpha(m)
            save(down(img), f"time/{name}/{ch}.png")
        # colon
        acc = K.THEMES["night" if name == "night" else ("mono" if name == "mono" else "color")]["accent"]
        cimg = Image.new("RGBA", (colon_w * S, cell_h * S), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cimg)
        r = 0.04 * K.TIME_PX
        for dy in (-0.153 * K.TIME_PX, 0.153 * K.TIME_PX):
            cx, cy = colon_w / 2, ink_mid + dy
            cd.rounded_rectangle([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], radius=P(2), fill=acc + (255,))
        save(down(cimg), f"time/{name}/colon.png")
    # always-on outline digits
    for theme in THEME_NAMES:
        col = K.THEMES[theme]["aod_time"]
        for ch in "0123456789":
            img = Image.new("RGBA", (cell_w * S, cell_h * S), (0, 0, 0, 0))
            ImageDraw.Draw(img).text((0, base_y * S), ch, font=f, fill=(0, 0, 0, 0), anchor="ls",
                                     features=["tnum"], stroke_width=P(1.4), stroke_fill=col + (255,))
            save(down(img), f"aod/time_{theme}/{ch}.png")
        cimg = Image.new("RGBA", (colon_w * S, cell_h * S), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cimg)
        r = 0.035 * K.TIME_PX
        for dy in (-0.153 * K.TIME_PX, 0.153 * K.TIME_PX):
            cx, cy = colon_w / 2, ink_mid + dy
            cd.rounded_rectangle([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], radius=P(2), fill=col + (255,))
        save(down(cimg), f"aod/time_{theme}/colon.png")
    return {**tm, "cell_w": cell_w, "cell_h": cell_h, "colon_w": colon_w, "ink_mid": ink_mid}


# ============================================================================= icons
def glance_x(name):
    """Centre x of a status icon in the band (GLANCE_MODE "row" or "split")."""
    gs = K.GLANCE_SIZE
    if K.GLANCE_MODE == "row":
        n = len(K.GLANCES)
        row_w = n * gs + (n - 1) * K.GLANCE_ROW_GAP
        return K.C - row_w / 2 + K.GLANCES.index(name) * (gs + K.GLANCE_ROW_GAP) + gs / 2
    # split: each pair centred between the separator and the widest condition name
    widest = max(F.advance(F.TEXT_FONT, K.DESC_PX, d) for _, d in K.WEATHER if d)
    inner = K.C - widest / 2 - 6                 # keep 6px from the text
    outer = K.SEP_X[0] + 4                       # and clear of the separator stroke
    pair_w = 2 * gs + K.GLANCE_PAIR_GAP
    left_cx = (outer + inner) / 2
    for side, pair in enumerate(K.GLANCE_SPLIT):
        if name in pair:
            cx = left_cx if side == 0 else K.W - left_cx
            return cx - pair_w / 2 + pair.index(name) * (gs + K.GLANCE_PAIR_GAP) + gs / 2
    raise ValueError(name)


def band_colour_at(theme, x):
    """The band's (noise-free) gradient colour at x, or black for themes without a band fill."""
    band = K.THEMES[theme]["band"]
    if band is None:
        return (0, 0, 0)
    f = (abs(x / K.W - 0.5) * 2) ** 1.4
    return lerp(band[0], band[1], f)



def metric_rgb(theme, metric):
    if theme == "color":
        return K.hexrgb(K.METRICS[metric][1])
    return K.THEMES[theme]["metric"]


def make_icons():
    for theme in THEME_NAMES:
        for metric in list(METRIC_SVG):
            base = metric if metric in K.METRICS else "sun"
            rgb = metric_rgb(theme, base)
            svg = METRIC_SVG[metric]("#%02x%02x%02x" % rgb)
            save(svg_to_image(svg, K.ICON_PX), f"icons/{theme}/{metric}.png")
        for i, (kind, _) in enumerate(K.WEATHER):
            img = retint(svg_to_image(weather_svg(kind), K.WEATHER_ICON_PX), theme, K.THEMES[theme].get("metric"))
            save(img, f"weather/{theme}/{i}.png")
            small = retint(svg_to_image(weather_svg(kind), K.ICON_PX), theme, K.THEMES[theme].get("metric"))
            save(small, f"icons/{theme}/weather_{i}.png")
        for level, hx in K.BATTERY_COLORS.items():
            rgb = K.hexrgb(hx) if theme == "color" else K.THEMES[theme]["metric"]
            save(svg_to_image(BATTERY_SVG("#%02x%02x%02x" % rgb), K.BATTERY_ICON_PX), f"battery/{theme}/{level}.png")
        for name, svg in GLANCE_SVG.items():
            img = retint(svg_to_image(svg, K.GLANCE_SIZE), theme, K.THEMES[theme].get("metric"))
            # the active icon covers the always-drawn off icon, so it sits on a disc of the
            # band colour at its position (the disc then doesn't show)
            if K.SECTION_LAYOUT == "corners":       # in the band, near the separators
                disc = band_colour_at(theme, K.SEP_X[0] + 22 if K.GLANCES.index(name) % 2 == 0 else K.SEP_X[1] - 22)
            elif K.SECTION_LAYOUT:                     # on a black panel
                disc = (0, 0, 0)
            else:
                disc = band_colour_at(theme, glance_x(name))
            backed = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(backed).ellipse([0, 0, img.width - 1, img.height - 1], fill=disc + (255,))
            backed.alpha_composite(img)
            save(backed, f"status/{theme}/{name}.png")
            off = retint(svg_to_image(GLANCE_OFF_SVG[name], K.GLANCE_SIZE), theme, K.THEMES[theme].get("muted_icon"))
            save(off, f"status/{theme}/{name}_off.png")
    # always-on battery icon (dim, single colour per theme)
    for theme in THEME_NAMES:
        rgb = K.THEMES[theme]["aod_text"]
        save(svg_to_image(BATTERY_SVG("#%02x%02x%02x" % rgb), K.BATTERY_ICON_PX), f"aod/battery_{theme}.png")


# ============================================================================= weather condition text
def make_desc_images(box):
    """One image per weather condition and theme, for an IMG_LEVEL bound to WEATHER_CURRENT.

    Face code can't read the current condition on API level 1, but a bound IMG_LEVEL is
    given it by the firmware, so the condition name is drawn as images."""
    asc, desc = F.vmetrics(str(F.TEXT_FONT))
    px = K.DESC_PX
    line_h = (asc + desc) * px
    baseline = (box["h"] - line_h) / 2 + asc * px           # same placement as a TEXT widget
    f = F.pil_font(str(F.TEXT_FONT), px, S)
    for theme in THEME_NAMES:
        col = K.THEMES[theme]["desc"]
        for i, (_, text) in enumerate(K.WEATHER):
            img = Image.new("RGBA", (box["w"] * S, box["h"] * S), (0, 0, 0, 0))
            if text:
                ImageDraw.Draw(img).text((img.width / 2, baseline * S), text, font=f, fill=col + (255,), anchor="ms")
            save(down(img), f"desc/{theme}/{i}.png")
    return dict(x=int(round(box["x"])), y=box["y"], w=box["w"], h=box["h"])


# ============================================================================= layout maths
def text_box(px, cx, ink_cy, w, sample="0123456789"):
    y, h = F.text_box_for_ink_centre(F.TEXT_FONT, px, ink_cy, sample)
    return dict(x=round(cx - w / 2, 1), y=y, w=w, h=h, size=px)


def digit_h(px):
    _, t, _, b = F.ink_extent(F.TEXT_FONT, px, "0123456789")
    return b - t


def cap_h(px):
    _, t, _, b = F.ink_extent(F.TEXT_FONT, px, "HEOTX")
    return b - t


def solve_side_x():
    """Centre x for the corner values: a 5-digit value ("99,999") gets equal gaps to the
    divider stroke and to the inner end of the long ticks."""
    x0, t, x1, b = F.ink_extent(F.TEXT_FONT, K.VALUE_PX, "99,999")
    w = x1 - x0
    h = digit_h(K.VALUE_PX)
    ring_in = K.RING_R - K.TICK_MAJOR
    div_edge = K.DIV_X[0] - 1
    y_top = K.ELBOW_Y
    lo, hi = 60.0, 180.0
    for _ in range(60):
        cx = (lo + hi) / 2
        xa, xb = cx - w / 2, cx + w / 2
        rg = min(ring_in - math.hypot(xa - K.C, y - K.C) for y in (y_top, y_top + h))
        if rg < div_edge - xb:
            lo = cx
        else:
            hi = cx
    cx = (lo + hi) / 2
    gap = div_edge - (cx + w / 2)
    return round(cx, 1), round(w, 1), round(gap, 1)


def char_widths(px):
    chars = "0123456789,.-:%° kmi"
    return {c: round(F.advance(F.TEXT_FONT, px, c), 2) for c in chars}


def build_layout(tm, bg_paths):
    L = {}
    segs = G.ring_segments()
    # ---------------------------------------------------------------- gauges
    gauges = []
    for slot, si in enumerate(G.SLOT_SEGMENT):
        ticks = []
        marker_at = None
        for t in G.segment_ticks(segs[si]):
            arc = G.tick_arc(t)
            if arc is None:                    # centre line: the marker sits here
                marker_at = len(ticks)
                continue
            major = round(t) % K.TICK_MAJOR_EVERY == 0
            L_ = K.TICK_MAJOR if major else K.TICK_MINOR
            ticks.append(dict(s=arc[0], e=arc[1], len=L_,
                              r_center=round(K.RING_R - L_ / 2, 1), r_outer=K.RING_R))
        g = dict(ticks=ticks)
        if marker_at is not None:              # lit once the fill passes the centre line
            g["marker"] = "top" if si == 1 else "bottom"
            g["marker_after"] = marker_at
        gauges.append(g)
    L["markers"] = make_markers()
    L["gauge"] = dict(segments=gauges)

    # ---------------------------------------------------------------- complications
    side_x, w99, side_gap = solve_side_x()
    vh = digit_h(K.VALUE_PX)
    top_value_cy = K.ELBOW_Y + vh / 2
    top_icon_cy = K.ELBOW_Y - K.ICON_GAP - K.ICON_PX / 2
    bm_lo = K.BAND_IN[1] + 1
    bm_hi = K.C + K.RING_R - K.TICK_MAJOR
    bm_cy = (bm_lo + bm_hi) / 2
    block = K.ICON_PX + K.ICON_GAP + vh
    bm_icon_cy = bm_cy - block / 2 + K.ICON_PX / 2
    bm_value_cy = bm_cy + block / 2 - vh / 2
    slots = []
    centres = [
        (side_x, top_icon_cy, top_value_cy),                         # TL
        (K.W - side_x, top_icon_cy, top_value_cy),                   # TR
        (side_x, K.W - top_icon_cy, K.W - top_value_cy),             # BL
        (K.C, bm_icon_cy, bm_value_cy),                              # BM
        (K.W - side_x, K.W - top_icon_cy, K.W - top_value_cy),       # BR
        (K.C, K.W - bm_icon_cy, K.W - bm_value_cy),                  # TM (mirrors BM: icon nearest the band)
    ]
    section = None
    if K.SECTION_LAYOUT:
        # status-icon row hugging one side of the band; the weather section gets three rows:
        # icon (nearest the band), temperature, condition text (outermost)
        gs, sg = K.GLANCE_SIZE, K.SECTION_GAP
        dh22_ = cap_h(K.DESC_PX)
        marker_tip = K.C - (K.RING_R - 13)            # top marker tip y; bottom mirrors
        def three_rows_down(lo, hi):                   # top section: desc, value, icon (towards band)
            g = (hi - lo - dh22_ - vh - K.ICON_PX) / 4
            d = lo + g + dh22_ / 2
            v = lo + 2 * g + dh22_ + vh / 2
            i = lo + 3 * g + dh22_ + vh + K.ICON_PX / 2
            return d, v, i
        if K.SECTION_LAYOUT == "glances_bottom":
            row_cy = K.BAND_IN[1] + sg + gs / 2
            lo, hi = row_cy + gs / 2, bm_hi
            cy = (lo + hi) / 2
            centres[3] = (K.C, cy - block / 2 + K.ICON_PX / 2, cy + block / 2 - vh / 2)
            d, v, i = three_rows_down(marker_tip, K.BAND_IN[0])
            centres[5] = (K.C, i, v)
            section = dict(row_cy=row_cy, desc_cy=d)
        elif K.SECTION_LAYOUT == "corners":
            # top-middle keeps its normal spot; the status icons go in the band's four corners
            # around the time. Bottom section: weather icon top-aligned with the bottom
            # corners' value ink, temperature below it, condition text centred between the
            # temperature and the bottom marker's tip.
            icon_top = K.W - top_value_cy - vh / 2
            i = icon_top + K.ICON_PX / 2
            v = icon_top + K.ICON_PX + K.ICON_GAP + vh / 2
            d = ((v + vh / 2) + (K.W - marker_tip)) / 2
            centres[3] = (K.C, i, v)
            section = dict(row_cy=None, desc_cy=d, corners=True)
        else:  # glances_top
            row_cy = K.BAND_IN[0] - sg - gs / 2
            lo, hi = marker_tip, row_cy - gs / 2
            cy = (lo + hi) / 2
            centres[5] = (K.C, cy + block / 2 - K.ICON_PX / 2, cy - block / 2 + vh / 2)
            d, v, i = three_rows_down(marker_tip, K.BAND_IN[0])
            centres[3] = (K.C, K.W - i, K.W - v)
            section = dict(row_cy=row_cy, desc_cy=K.W - d)
    asc, desc = F.vmetrics(str(F.TEXT_FONT))
    for cx, icy, vcy in centres:
        vbox = text_box(K.VALUE_PX, cx, vcy, 132)
        # unit box: shares the value's baseline
        v_line_h = (asc + desc) * K.VALUE_PX
        baseline = vbox["y"] + (vbox["h"] - v_line_h) / 2 + asc * K.VALUE_PX
        u_line_h = (asc + desc) * K.UNIT_PX
        u_h = int(round(u_line_h + 6))
        u_y = baseline - asc * K.UNIT_PX - (u_h - u_line_h) / 2
        top_y = min(icy - K.ICON_PX / 2, vcy - vh / 2) - 8
        bot_y = max(icy + K.ICON_PX / 2, vcy + vh / 2) + 8
        slots.append(dict(
            cx=round(cx, 1),
            icon=dict(x=round(cx - K.ICON_PX / 2), y=round(icy - K.ICON_PX / 2), size=K.ICON_PX),
            value=vbox,
            unit=dict(y=round(u_y, 1), h=u_h, size=K.UNIT_PX),
            edit=dict(x=round(cx - 58), y=round(top_y), w=116, h=round(bot_y - top_y)),
        ))
    L["slots"] = slots
    L["char_widths"] = dict(value=char_widths(K.VALUE_PX), unit=char_widths(K.UNIT_PX), unit_gap=3)

    # ---------------------------------------------------------------- date stack (left of the time)
    small = K.DATE_DAY_PX if K.DATE_LARGE else K.DATE_SMALL_PX
    ch21, dh42 = cap_h(small), digit_h(K.DATE_DAY_PX)
    # gaps shrink from the approved 11.1/10.1 (21px lines) to 8/8 (42px lines)
    t_ = (small - 21) / 21
    gap1, gap2 = 11.1 + (8 - 11.1) * t_, 10.1 + (8 - 10.1) * t_
    stack_h = ch21 + gap1 + dh42 + gap2 + ch21

    def date_lines(cx, top):
        return dict(
            dow=text_box(small, cx, top + ch21 / 2, 100, "HEOTX"),
            day=text_box(K.DATE_DAY_PX, cx, top + ch21 + gap1 + dh42 / 2, 100),
            month=text_box(small, cx, top + ch21 + gap1 + dh42 + gap2 + ch21 / 2, 100, "HEOTX"),
        )
    side_l = K.SEP_X[0] / 2
    side_r = (K.SEP_X[1] + K.W) / 2
    top = K.MID - stack_h / 2
    L["date"] = date_lines(side_l, top)
    L["theme_edit"] = dict(x=round(side_l - 44), y=round(top - 10), w=88, h=round(stack_h + 20))

    bh = digit_h(K.BATTERY_VALUE_PX)
    bat_ink = K.BATTERY_ICON_PX * 10 / 24                 # the glyph's drawn height
    blk = bat_ink + K.SIDE_BLOCK_GAP + bh
    btop = K.MID - blk / 2
    L["battery"] = dict(
        icon=dict(x=round(side_r - K.BATTERY_ICON_PX / 2), y=round(btop + bat_ink / 2 - K.BATTERY_ICON_PX / 2), size=K.BATTERY_ICON_PX),
        text=text_box(K.BATTERY_VALUE_PX, side_r, btop + bat_ink + K.SIDE_BLOCK_GAP + bh / 2, 100),
    )

    # ---------------------------------------------------------------- time + description
    dh22 = cap_h(K.DESC_PX)
    th = tm["bot"] - tm["top"]
    total_adv = 4 * tm["adv"] + tm["colon_w"]
    worst_w = total_adv - tm["lsb_min"] - (tm["adv"] - tm["right_max"])
    gh = (K.SEP_X[1] - 1 - (K.SEP_X[0] + 1) - worst_w) / 2
    gs = K.GLANCE_SIZE
    if section:
        # the time is alone in the band, centred
        gv = (K.BAND_IN[1] - K.BAND_IN[0] - th) / 2
        time_cy = K.MID
        desc_cy, row_cy = section["desc_cy"], section["row_cy"]
        if section.get("corners"):
            # each icon sits in the corner between the band edge and the separator's flared
            # end, the same distance g from both (measured to a 22px circle around the icon);
            # g is the largest that keeps CORNER_TIME_CLEAR from the time's ink
            th_top, th_bot = time_cy - th / 2, time_cy + th / 2
            (fx1, fy1), (fx2, fy2) = G.separator_points(0)[:2]
            theta = math.atan2(abs(fx2 - fx1), fy2 - fy1)
            r = gs / 2
            def spot(g):
                cy = K.BAND_IN[0] + r + g
                xl = fx1 + (fx2 - fx1) * (cy - fy1) / (fy2 - fy1)
                return xl + (r + g) / math.cos(theta), cy
            g = max(gg / 4 for gg in range(0, 64) if spot(gg / 4)[1] + r <= th_top - K.CORNER_TIME_CLEAR)
            cx_l, cy_t = spot(g)
            cy_b = K.W - cy_t
            spots = [(cx_l, cy_t), (K.W - cx_l, cy_t), (cx_l, cy_b), (K.W - cx_l, cy_b)]
            L["_notes_corner_gap"] = round(g, 2)
            L["glances"] = [dict(name=nm, x=round(x - gs / 2), y=round(y - gs / 2)) for nm, (x, y) in zip(K.GLANCES, spots)]
    elif K.GLANCE_MODE == "row":
        # status-icon row, time and condition stacked in the band with four equal gaps
        gv = (K.BAND_IN[1] - K.BAND_IN[0] - gs - th - dh22) / 4
        row_cy = K.BAND_IN[0] + gv + gs / 2
        time_cy = K.BAND_IN[0] + 2 * gv + gs + th / 2
        desc_cy = K.BAND_IN[0] + 3 * gv + gs + th + dh22 / 2
    else:
        # split: time and condition with three equal gaps; the icons share the condition's row
        gv = (K.BAND_IN[1] - K.BAND_IN[0] - th - dh22) / 3
        time_cy = K.BAND_IN[0] + gv + th / 2
        desc_cy = K.BAND_IN[0] + 2 * gv + th + dh22 / 2
        row_cy = desc_cy
    if not (section and section.get("corners")):
        L["glances"] = [dict(name=nm, x=round(glance_x(nm) - gs / 2), y=round(row_cy - gs / 2)) for nm in K.GLANCES]
    x0 = K.C - (4 * tm["cell_w"] + tm["colon_w"]) / 2
    img_y = time_cy - tm["ink_mid"]
    L["time"] = dict(
        hour_x=round(x0), minute_x=round(x0 + 2 * tm["cell_w"] + tm["colon_w"]),
        colon_x=round(x0 + 2 * tm["cell_w"]), y=round(img_y),
        cell_w=tm["cell_w"], cell_h=tm["cell_h"], gap_side=round(gh, 1), gap_vertical=round(gv, 1),
    )
    L["desc"] = text_box(K.DESC_PX, K.C, desc_cy, 260, "HEOTX")
    L["desc_img"] = make_desc_images(L["desc"])
    L["night_edit"] = dict(x=round(K.C - 115), y=round(time_cy - 52), w=230, h=104)

    # ---------------------------------------------------------------- always-on
    L["aod"] = dict(date=date_lines(side_l, K.MID - stack_h / 2),
                    battery=L["battery"])

    # ---------------------------------------------------------------- colours / misc
    colours = {}
    for theme in THEME_NAMES:
        t = K.THEMES[theme]
        m = {}
        for metric in K.METRICS:
            rgb = metric_rgb(theme, metric)
            m[metric] = dict(on=hexint(rgb), dim=hexint(lerp((0, 0, 0), rgb, t["dim_factor"])))
        colours[theme] = dict(text=hexint(t["text"]), muted=hexint(t["muted"]), accent=hexint(t["accent"]),
                              desc=hexint(t["desc"]), aod_text=hexint(t["aod_text"]),
                              unit=m, bg=bg_paths[theme], aod_bg=bg_paths[f"aod_{theme}"])
    L["colors"] = colours
    L["metrics"] = {k: dict(title=v[0], progress=v[2]) for k, v in K.METRICS.items()}
    L["default_slots"] = K.DEFAULT_SLOTS
    L["weather_desc"] = [d for _, d in K.WEATHER]
    L["font"] = "fonts/" + F.TEXT_FONT_SUBSET_NAME
    L["_notes"] = dict(glance_mode=K.GLANCE_MODE, side_value_x=side_x, width_99999=w99, gap_99999_to_divider=side_gap,
                       time_px=K.TIME_PX, time_gap_side=round(gh, 1), time_gap_vertical=round(gv, 1))
    return L


def write_layout(L):
    body = json.dumps(L, indent=2)
    K.LAYOUT_JS.write_text(
        "// GENERATED by faces/sextant/design/generate.py - do not edit by hand.\n"
        "// Change faces/sextant/design/config.py and re-run the generator (npm run assets).\n"
        f"export const LAYOUT = {body};\n")


# ============================================================================= edit-mode assets
def make_edit_assets(L):
    def frame(w, h, col, width):
        img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        ImageDraw.Draw(img).rounded_rectangle([P(1), P(1), P(w - 1), P(h - 1)], radius=P(14), outline=col, width=P(width))
        return down(img)
    sizes = {(s["edit"]["w"], s["edit"]["h"]) for s in L["slots"]}
    sizes.add((L["theme_edit"]["w"], L["theme_edit"]["h"]))
    sizes.add((L["night_edit"]["w"], L["night_edit"]["h"]))
    for w, h in sizes:
        save(frame(w, h, (214, 172, 96, 255), 3), f"edit/select_{w}x{h}.png")
        save(frame(w, h, (120, 128, 140, 200), 2), f"edit/unselect_{w}x{h}.png")
    # The firmware draws the tip text in its own (dark) colour, so the tip is light.
    tip = Image.new("RGBA", (150 * S, 40 * S), (0, 0, 0, 0))
    ImageDraw.Draw(tip).rounded_rectangle([0, 0, tip.width - 1, tip.height - 1], radius=P(20), fill=(240, 216, 160, 255), outline=(255, 244, 214, 255), width=P(2))
    save(down(tip), "edit/tip.png")
    # The firmware hides normal widgets in edit mode, so give the edit boxes a dimmed
    # copy of the face's background (shown only in edit mode) for context.
    for theme in K.THEMES:
        bg = Image.open(OUT / "bg" / f"{theme}.png").convert("RGBA")
        save(Image.eval(bg.convert("RGB"), lambda v: int(v * 0.45)).convert("RGBA"), f"edit/bg_{theme}.png")

    # per-metric previews: icon above a sample value
    samples = dict(steps="8,412", heart="72", distance="5.86", calories="486", floors="7", pai="64", stand="9",
                   fatburn="23", spo2="98%", stress="27", uvi="3", humidity="61%", aqi="42", sun="18:21", weather="18°")
    w, h = L["slots"][0]["edit"]["w"], L["slots"][0]["edit"]["h"]
    f = F.pil_font(str(F.TEXT_FONT), 34, S)
    for metric, txt in samples.items():
        img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        svg = weather_svg("partly_day") if metric == "weather" else METRIC_SVG[metric]("#%02x%02x%02x" % K.hexrgb(K.METRICS[metric][1]))
        icon = svg_to_image(svg, 28 * S)
        img.alpha_composite(icon, (img.width // 2 - icon.width // 2, P(8)))
        ImageDraw.Draw(img).text((img.width // 2, P(h - 14)), txt, font=f, fill=(244, 246, 248, 255), anchor="ms")
        save(down(img), f"edit/preview_{metric}.png")
    # theme + night previews
    tw, th_ = L["theme_edit"]["w"], L["theme_edit"]["h"]
    fs = F.pil_font(str(F.TEXT_FONT), 20, S)
    for name, label, col in (("color", "COLOR", (214, 172, 96)), ("mono", "MONO", (230, 232, 236))):
        img = Image.new("RGBA", (tw * S, th_ * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([P(tw / 2 - 16), P(14), P(tw / 2 + 16), P(46)], fill=col + (255,))
        d.text((img.width // 2, P(th_ - 16)), label, font=fs, fill=(244, 246, 248, 255), anchor="ms")
        save(down(img), f"edit/preview_theme_{name}.png")
    nw, nh = L["night_edit"]["w"], L["night_edit"]["h"]
    fm = F.pil_font(str(F.TEXT_FONT), 24, S)
    for name, label, col in (("auto", "NIGHT MODE: AUTO", (232, 44, 26)), ("off", "NIGHT MODE: OFF", (150, 160, 172))):
        img = Image.new("RGBA", (nw * S, nh * S), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((img.width // 2, img.height // 2), label, font=fm, fill=col + (255,), anchor="mm")
        save(down(img), f"edit/preview_night_{name}.png")


# ============================================================================= main
def generate():
    F.build_fonts()
    # keep icon.png / cover.png (written by `npm run screenshots`), rebuild the rest
    OUT.mkdir(parents=True, exist_ok=True)
    for child in OUT.iterdir():
        if child.name in ("icon.png", "cover.png"):
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    F.write_watch_font(OUT / "fonts" / F.TEXT_FONT_SUBSET_NAME)
    K.TIME_PX = solve_time_px()
    bg = make_backgrounds()
    tm = make_time_digits()
    make_icons()
    L = build_layout(tm, bg)
    make_edit_assets(L)
    write_layout(L)
    return L
