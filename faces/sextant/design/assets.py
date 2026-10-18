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
            col = lerp(t["glow_lo"], t["accent"], K.BRASS_FLOOR + (1 - K.BRASS_FLOOR) * max(0, f) ** 1.8)
            d.line([P(xa), P(fn(xa)), P(xb), P(fn(xb))], fill=col, width=P(K.LINE_W))


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
            d.line([(P(x), P(y)) for x, y in pts], fill=col, width=P(K.LINE_W), joint="curve")


def draw_separators(d, col, theme=None):
    """Band separators. With SEPARATOR_BRASS (and a theme) they take the band edges' look:
    brass in the middle fading to the dim edge colour at the ends."""
    for i in (0, 1):
        pts = G.separator_points(i)
        if not (K.SEPARATOR_BRASS and theme):
            d.line([(P(x), P(y)) for x, y in pts], fill=col, width=P(K.LINE_W), joint="curve")
            continue
        t = K.THEMES[theme]
        segs = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            n = 40
            segs += [((x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n), (x1 + (x2 - x1) * (k + 1) / n, y1 + (y2 - y1) * (k + 1) / n)) for k in range(n)]
        half = (pts[-1][1] - pts[0][1]) / 2
        for (xa, ya), (xb, yb) in segs:
            f = 1 - abs((ya + yb) / 2 - K.MID) / half
            d.line([P(xa), P(ya), P(xb), P(yb)], fill=lerp(t["glow_lo"], t["accent"], K.BRASS_FLOOR + (1 - K.BRASS_FLOOR) * max(0, f) ** 1.8), width=P(K.LINE_W))


def tick_line(d, deg, col, length, r_out=K.RING_R, width=K.TICK_WIDTH):
    ca, sa = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    d.line([P(K.C + r_out * ca), P(K.C + r_out * sa),
            P(K.C + (r_out - length) * ca), P(K.C + (r_out - length) * sa)], fill=col, width=P(width))




RULE_PTS = {}


def rule_points(y, top):
    """Polyline for the rule between a status pair and its metric (RULE_STYLE).
    short: a SECTION_RULE_W rule. long: reaches RULE_END_GAP from the dividers' vertical parts.
    flare_out / flare_in: a flat middle whose ends bend toward the rim / the band, along the
    line from the flat end to the divider's elbow (mirrored for flare_in)."""
    st = K.RULE_STYLE.replace("_brass", "")
    edge = G.DIV_X[0] + K.LINE_W / 2 + K.RULE_END_GAP          # where every long rule stops
    if st == "short":
        h = K.SECTION_RULE_W / 2
        return [(K.C - h, y), (K.C + h, y)]
    if st == "long":
        return [(edge, y), (K.W - edge, y)]
    ey = G.DIV_ELBOW_Y if top else K.W - G.DIV_ELBOW_Y
    fx = K.C - K.RULE_FLAT / 2                                  # flat part's left end
    slope = (ey - y) / (G.DIV_X[0] - fx)                        # dy per unit x toward the elbow
    if st == "flare_in":
        slope = -slope
    yl = y + slope * (edge - fx)
    return [(edge, yl), (fx, y), (K.W - fx, y), (K.W - edge, yl)]


def rule_image(pts, theme, x0, y0):
    t = K.THEMES[theme]
    xs = [p[0] for p in pts]
    w = math.ceil(max(xs) - x0 + K.LINE_W)
    h = math.ceil(max(p[1] for p in pts) - y0 + K.LINE_W)
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    q = [(P(x - x0), P(y - y0)) for x, y in pts]
    if "brass" not in K.RULE_STYLE:
        d.line(q, fill=t["divider"] + (255,), width=P(K.LINE_W), joint="curve")
    else:
        half = (max(xs) - min(xs)) / 2
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            n = 40
            for k in range(n):
                a = (xa + (xb - xa) * k / n, ya + (yb - ya) * k / n)
                b = (xa + (xb - xa) * (k + 1) / n, ya + (yb - ya) * (k + 1) / n)
                f = 1 - abs((a[0] + b[0]) / 2 - K.C) / half
                col = lerp(t["glow_lo"], t["accent"], K.BRASS_FLOOR + (1 - K.BRASS_FLOOR) * max(0, f) ** 1.8)
                d.line([P(a[0] - x0), P(a[1] - y0), P(b[0] - x0), P(b[1] - y0)], fill=col, width=P(K.LINE_W))
    r = P(K.LINE_W / 2)
    for x, y in (q[0], q[-1]):                                  # round caps
        d.ellipse([x - r, y - r, x + r, y + r], fill=img.getpixel((max(0, min(img.width - 1, int(x))), max(0, min(img.height - 1, int(y))))))
    return down(img)


MARKER_TIP_R, MARKER_BASE_R, MARKER_HALF_W, MARKER_BOX = K.RING_R - 13, K.RING_R + 1, 5.0, 16


def marker_image(zepp_deg, col):
    """A triangle marker at zepp_deg (tip towards the centre), cut to a small box around it."""
    big = Image.new("RGBA", (K.W * S, K.W * S), (0, 0, 0, 0))
    a = math.radians(zepp_deg)
    ux, uy = math.sin(a), -math.cos(a)                 # outward
    vx, vy = math.cos(a), math.sin(a)                  # tangent
    tip = (K.C + MARKER_TIP_R * ux, K.C + MARKER_TIP_R * uy)
    bc = (K.C + MARKER_BASE_R * ux, K.C + MARKER_BASE_R * uy)
    pts = [tip, (bc[0] - MARKER_HALF_W * vx, bc[1] - MARKER_HALF_W * vy), (bc[0] + MARKER_HALF_W * vx, bc[1] + MARKER_HALF_W * vy)]
    ImageDraw.Draw(big).polygon([(P(x), P(y)) for x, y in pts], fill=col + (255,))
    cx, cy = K.C + (MARKER_TIP_R + MARKER_BASE_R) / 2 * ux, K.C + (MARKER_TIP_R + MARKER_BASE_R) / 2 * uy
    x0, y0 = int(round(cx - MARKER_BOX / 2)), int(round(cy - MARKER_BOX / 2))
    crop = big.crop((x0 * S, y0 * S, (x0 + MARKER_BOX) * S, (y0 + MARKER_BOX) * S))
    return down(crop), x0, y0


def compass_angles():
    """Marker angles (zepp degrees). The diagonals sit half a degree off 45 so the
    whole-degree ticks either side are equally far away."""
    return {"progress": [0, 180], "brass2": [0, 180], "brass6": [0, 45.5, 134.5, 180, 225.5, 314.5],
            "brass8": [0, 45.5, 90, 134.5, 180, 225.5, 270, 314.5]}[K.MARKERS]


def make_markers():
    """Triangle markers (tip towards the centre) at compass_angles(). Images, because the
    firmware draws arcs only in whole degrees. For each marker k and theme:
    m{k}_brass, and m{k}_lit_{metric} / m{k}_dim_{metric} for markers that follow a gauge."""
    out = []
    for k, ang in enumerate(compass_angles()):
        for theme in THEME_NAMES:
            t = K.THEMES[theme]
            img, x0, y0 = marker_image(ang, t["accent"])
            save(img, f"marker/{theme}/m{k}_brass.png")
            if K.MARKERS in ("progress", "brass6"):
                for metric in K.METRICS:
                    rgb = metric_rgb(theme, metric)
                    save(marker_image(ang, rgb)[0], f"marker/{theme}/m{k}_lit_{metric}.png")
                    if K.MARKERS == "progress":
                        save(marker_image(ang, lerp((0, 0, 0), rgb, t["dim_factor"]))[0], f"marker/{theme}/m{k}_dim_{metric}.png")
        out.append(dict(k=k, a=ang, x=x0, y=y0))
    return out


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
        draw_separators(d, K.THEMES[theme]["divider"], theme)
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



def centred(img, size):
    """The icon's drawing centred in a size x size box. Icon art doesn't always sit in the
    middle of its canvas, which made the icon-to-value gaps look uneven."""
    bb = img.getchannel("A").getbbox()
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if not bb:
        return out
    art = img.crop(bb)
    out.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
    return out


def battery_ink_h():
    img = centred(svg_to_image(BATTERY_SVG("#ffffff"), K.BATTERY_ICON_PX), K.BATTERY_ICON_PX)
    bb = img.getchannel("A").getbbox()
    return bb[3] - bb[1]


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
            save(centred(svg_to_image(svg, K.ICON_PX), K.ICON_PX), f"icons/{theme}/{metric}.png")
        for i, (kind, _) in enumerate(K.WEATHER):
            img = retint(svg_to_image(weather_svg(kind), K.WEATHER_ICON_PX), theme, K.THEMES[theme].get("metric"))
            save(img, f"weather/{theme}/{i}.png")
            small = retint(svg_to_image(weather_svg(kind), K.ICON_PX), theme, K.THEMES[theme].get("metric"))
            save(centred(small, K.ICON_PX), f"icons/{theme}/weather_{i}.png")
        for level, hx in K.BATTERY_COLORS.items():
            rgb = K.hexrgb(hx) if theme == "color" else K.THEMES[theme]["metric"]
            save(centred(svg_to_image(BATTERY_SVG("#%02x%02x%02x" % rgb), K.BATTERY_ICON_PX), K.BATTERY_ICON_PX), f"battery/{theme}/{level}.png")
        for name, svg in GLANCE_SVG.items():
            img = centred(retint(svg_to_image(svg, K.GLANCE_SIZE), theme, K.THEMES[theme].get("metric")), K.GLANCE_SIZE)
            # the active icon covers the always-drawn off icon, so it sits on a disc of the
            # band colour at its position (the disc then doesn't show)
            if K.GLANCE_MODE == "sections":         # on the black section panels
                disc = (0, 0, 0)
            elif K.SECTION_LAYOUT == "corners":     # in the band, near the separators
                disc = band_colour_at(theme, K.SEP_X[0] + 22 if K.GLANCES.index(name) % 2 == 0 else K.SEP_X[1] - 22)
            elif K.SECTION_LAYOUT:                     # on a black panel
                disc = (0, 0, 0)
            else:
                disc = band_colour_at(theme, glance_x(name))
            backed = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(backed).ellipse([0, 0, img.width - 1, img.height - 1], fill=disc + (255,))
            backed.alpha_composite(img)
            save(backed, f"status/{theme}/{name}.png")
            off = centred(retint(svg_to_image(GLANCE_OFF_SVG[name], K.GLANCE_SIZE), theme, K.THEMES[theme].get("muted_icon")), K.GLANCE_SIZE)
            save(off, f"status/{theme}/{name}_off.png")
    # always-on battery icon (dim, single colour per theme)
    for theme in THEME_NAMES:
        rgb = K.THEMES[theme]["aod_text"]
        save(centred(svg_to_image(BATTERY_SVG("#%02x%02x%02x" % rgb), K.BATTERY_ICON_PX), K.BATTERY_ICON_PX), f"aod/battery_{theme}.png")


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


# ============================================================================= rotated corners (mock)
ROT_SET = {0: "n", 1: "p", 2: "p", 4: "n"}     # slot -> rotation set (TL, TR, BL, BR)
ROT_CHARS = {**{str(d): str(d) for d in range(10)}, ",": "comma", ".": "dot", "-": "dash", ":": "colon"}
ROT_UNIT_CHARS = "kmi"


def corner_alpha():
    """Angle (deg) of the corner gauges' mid-point from the nearest centre line."""
    t = list(G.segment_ticks(G.ring_segments()[0]))
    # the extra tick extends the divider end by one step; each tick covers [z - 1, z] here
    mid = (G.to_zepp(t[0]) + (K.TICK_STEP if K.CORNER_EXTRA_TICK else 0) + G.to_zepp(t[-1])) / 2 - 0.5
    return 360 - mid


def rot_rho(name):
    return -corner_alpha() if name == "n" else corner_alpha()


def rot_q(px):
    return int(math.ceil(px * 1.7 / 2)) * 2


def rot_glyph(c, px, rgb):
    """One upright glyph on a square canvas whose centre sits on the value's ink centre
    line (horizontally: the middle of the glyph's advance). The face code places one
    per character along the gauge and the firmware turns it (IMG `angle`), so every
    glyph of a value, and its unit, shares one anchor line."""
    q = rot_q(K.VALUE_PX)
    _, top, _, bot = F.ink_extent(F.TEXT_FONT, K.VALUE_PX, "0123456789")
    img = Image.new("RGBA", (q * S, q * S), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((q * S / 2, q * S / 2 - (top + bot) / 2 * S), c, font=F.pil_font(F.TEXT_FONT, px, S),
                             fill=tuple(rgb) + (255,), anchor="ms")
    return down(img)


def make_rot_assets():
    """CORNER_ROTATE: one image per character and theme (the firmware rotates them)."""
    if not K.CORNER_ROTATE:
        return
    for theme in THEME_NAMES:
        t = K.THEMES[theme]
        for c, code in ROT_CHARS.items():
            save(rot_glyph(c, K.VALUE_PX, t["text"]), f"rot/{theme}/{code}.png")
        for c in ROT_UNIT_CHARS:
            save(rot_glyph(c, K.UNIT_PX, metric_rgb(theme, "distance")), f"rot/{theme}/u_distance_{c}.png")
    Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(OUT / "rot" / "blank.png")


def rotate_corners(centres, slots):
    """CORNER_ROTATE: each corner takes the top- (or bottom-) middle layout turned about the
    centre to its gauge's mid-angle, so its value keeps the same gap to the ticks."""
    a = corner_alpha()
    tm, bm = centres[5], centres[3]
    for i, name in ROT_SET.items():
        rho = rot_rho(name)
        base = tm if i in (0, 1) else bm
        ca, sa = math.cos(math.radians(rho)), math.sin(math.radians(rho))
        def turn(y):
            dy = y - K.C
            return K.C - dy * sa, K.C + dy * ca
        vx, vy = turn(base[2])
        ix, iy = turn(base[1])
        box = slots[i]
        box["cx"] = round(vx, 1)
        box["value"] = text_box(K.VALUE_PX, vx, vy, 132)            # upright fallback (bound metrics)
        box["unit"]["y"] = round(box["unit"]["y"] - centres[i][2] + vy, 1)
        box["icon"] = dict(x=round(ix - K.ICON_PX / 2), y=round(iy - K.ICON_PX / 2), size=K.ICON_PX)
        rot = dict(deg=round(rho, 2), cos=round(ca, 5), sin=round(sa, 5), vx=round(vx, 2), vy=round(vy, 2), q=rot_q(K.VALUE_PX))
        if K.CORNER_ROTATE == "text_icon":
            # the icon turns too: a widget box big enough for the turned drawing
            qi = int(math.ceil(K.ICON_PX * (abs(ca) + abs(sa)) / 2)) * 2 + 2
            rot["icon"] = dict(x=round(ix - qi / 2), y=round(iy - qi / 2), box=qi, pos=(qi - K.ICON_PX) // 2)
        box["rot"] = rot
        mx, my = (vx + ix) / 2, (vy + iy) / 2
        e = box["edit"]
        box["edit"] = dict(x=round(mx - e["w"] / 2), y=round(my - e["h"] / 2), w=e["w"], h=e["h"])
    return a


def build_layout(tm, bg_paths):
    L = {}
    segs = G.ring_segments()
    # ---------------------------------------------------------------- gauges
    gauges = []
    markers = make_markers()
    follow = K.MARKERS in ("progress", "brass6")
    for slot, si in enumerate(G.SLOT_SEGMENT):
        seg_ticks = list(G.segment_ticks(segs[si]))
        if K.CORNER_EXTRA_TICK and si in (0, 2, 3, 5):
            # corner gauges start at their divider: one more tick there
            step = K.TICK_STEP if seg_ticks[1] < seg_ticks[0] else -K.TICK_STEP
            seg_ticks.insert(0, seg_ticks[0] + step)
        lo_z, hi_z = sorted((G.to_zepp(seg_ticks[0]), G.to_zepp(seg_ticks[-1])))
        if hi_z - lo_z > 180:                          # the top gauge straddles 0
            lo_z, hi_z = hi_z - 360, lo_z
        mine = [m for m in markers if lo_z - 0.01 <= ((m["a"] + 180 - (lo_z + hi_z) / 2) % 360 - 180 + (lo_z + hi_z) / 2) <= hi_z + 0.01]
        near = {round(m["a"] - 0.5) % 360 for m in mine if m["a"] % 1} | {round(m["a"] + 0.5) % 360 for m in mine if m["a"] % 1}
        ticks, marker_at = [], None
        for t in seg_ticks:
            z = round(G.to_zepp(t)) % 360
            arc = G.tick_arc(t)
            if arc is None or z in near or z in {(round(m["a"] - 1.5)) % 360 for m in mine if m["a"] % 1} | {(round(m["a"] + 1.5)) % 360 for m in mine if m["a"] % 1}:
                if marker_at is None:
                    marker_at = len(ticks)     # the marker sits here
                continue
            major = round(t) % K.TICK_MAJOR_EVERY == 0
            L_ = K.TICK_MAJOR if major else K.TICK_MINOR
            ticks.append(dict(s=arc[0], e=arc[1], len=L_,
                              r_center=round(K.RING_R - L_ / 2, 1), r_outer=K.RING_R))
        g = dict(ticks=ticks)
        if follow and mine and marker_at is not None:
            m = mine[0]
            g["marker"] = dict(k=m["k"], x=m["x"], y=m["y"], after=marker_at,
                               base="brass" if K.MARKERS == "brass6" else "dim")
        gauges.append(g)
    L["markers"] = dict(fixed=[m for m in markers if not follow or not any(
        g.get("marker", {}).get("k") == m["k"] for g in gauges)])
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
    # VALUE_BOX_DESCENDER: a value's box runs from the digits' top to a comma's bottom, so a
    # value above its icon keeps the full gap even with a thousands separator
    dsc = F.ink_extent(F.TEXT_FONT, K.VALUE_PX, ",")[3] if K.VALUE_BOX_DESCENDER else 0
    bm_icon_cy = bm_cy - block / 2 + K.ICON_PX / 2
    bm_value_cy = bm_cy + block / 2 - vh / 2
    slots = []
    centres = [
        (side_x, top_icon_cy, top_value_cy),                         # TL
        (K.W - side_x, top_icon_cy, top_value_cy),                   # TR
        (side_x, K.W - top_icon_cy + dsc, K.W - top_value_cy),       # BL
        (K.C, bm_icon_cy, bm_value_cy),                              # BM
        (K.W - side_x, K.W - top_icon_cy + dsc, K.W - top_value_cy), # BR
        (K.C, K.W - bm_icon_cy + dsc / 2, K.W - bm_value_cy - dsc / 2),  # TM (mirrors BM: icon nearest the band)
    ]
    sections_rows = None
    if K.GLANCE_MODE == "sections":
        # status-icon pairs hug the band in the top- and bottom-middle sections; those
        # sections' metrics move out so their outer edge is as far from the ticks as the
        # corner icons are (nearest icon-box corner to the ticks' inner end)
        tick_in = K.RING_R - K.TICK_MAJOR
        cx_, icy_ = centres[0][0], centres[0][1]
        corners_ = [(cx_ + dx, icy_ + dy) for dx in (-K.ICON_PX / 2, K.ICON_PX / 2) for dy in (-K.ICON_PX / 2, K.ICON_PX / 2)]
        rim_gap = tick_in - max(math.hypot(x - K.C, y - K.C) for x, y in corners_)
        gs = K.GLANCE_SIZE
        # the widest value ("99,999") keeps rim_gap from the ticks at its outer corners
        reach = math.sqrt((tick_in - rim_gap) ** 2 - (w99 / 2) ** 2)
        # TM: value (box incl. comma depth) on top, icon below it, status pair at the band
        v_top = K.C - reach
        tm_v = v_top + vh / 2
        tm_i = v_top + vh + dsc + K.ICON_GAP + K.ICON_PX / 2
        centres[5] = (K.C, tm_i, tm_v)
        # BM: mirror (icon at the top, value below; box bottom incl. comma depth)
        v_bot = K.C + reach
        bm_v = v_bot - dsc - vh / 2
        bm_i = bm_v - vh / 2 - K.ICON_GAP - K.ICON_PX / 2
        centres[3] = (K.C, bm_i, bm_v)
        sections_rows = dict(top=K.BAND_IN[0] - K.SECTION_GAP - gs / 2, bottom=K.BAND_IN[1] + K.SECTION_GAP + gs / 2)
        if K.SECTION_RULES:
            # a short rule midway between each status pair and its metric's icon box
            ry_t = ((tm_i + K.ICON_PX / 2) + (sections_rows["top"] - gs / 2)) / 2
            ry_b = ((bm_i - K.ICON_PX / 2) + (sections_rows["bottom"] + gs / 2)) / 2
            RULE_PTS.clear()
            L["rules"] = []
            for name, y in (("t", ry_t), ("b", ry_b)):
                pts = rule_points(y, name == "t")
                RULE_PTS[name] = pts
                pad = K.LINE_W
                L["rules"].append(dict(x=math.floor(min(p[0] for p in pts) - pad), y=math.floor(min(p[1] for p in pts) - pad), src=name))
        L["_notes_rim_gap"] = round(rim_gap, 1)
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
    if K.CORNER_ROTATE:
        L["_notes_corner_angle"] = round(rotate_corners(centres, slots), 2)
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
    # battery: the drawing is centred in its box and much shorter than it is wide, so
    # space it on the drawing itself, with the same visible gap as the complications
    bat_ink = battery_ink_h()
    blk = bat_ink + K.VISIBLE_ICON_GAP + bh
    btop = K.MID - blk / 2
    L["battery"] = dict(
        icon=dict(x=round(side_r - K.BATTERY_ICON_PX / 2), y=round(btop + bat_ink / 2 - K.BATTERY_ICON_PX / 2), size=K.BATTERY_ICON_PX),
        text=text_box(K.BATTERY_VALUE_PX, side_r, btop + bat_ink + K.VISIBLE_ICON_GAP + bh / 2, 100),
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
    elif K.GLANCE_MODE == "sections":
        # the band holds the time and the condition text, three equal gaps
        gv = (K.BAND_IN[1] - K.BAND_IN[0] - th - dh22) / 3
        time_cy = K.BAND_IN[0] + gv + th / 2
        desc_cy = K.BAND_IN[0] + 2 * gv + th + dh22 / 2
        row_cy = None
        spots = {}
        for key, pair in (("top", K.GLANCE_SECTIONS[0]), ("bottom", K.GLANCE_SECTIONS[1])):
            w_ = 2 * gs + K.GLANCE_ROW_GAP
            for k, nm in enumerate(pair):
                spots[nm] = (K.C - w_ / 2 + gs / 2 + k * (gs + K.GLANCE_ROW_GAP), sections_rows[key])
        L["glances"] = [dict(name=nm, x=round(spots[nm][0] - gs / 2), y=round(spots[nm][1] - gs / 2)) for nm in K.GLANCES]
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
    if not (section and section.get("corners")) and K.GLANCE_MODE != "sections":
        L["glances"] = [dict(name=nm, x=round(glance_x(nm) - gs / 2), y=round(row_cy - gs / 2)) for nm in K.GLANCES]
    x0 = K.C - (4 * tm["cell_w"] + tm["colon_w"]) / 2
    img_y = time_cy - tm["ink_mid"]
    L["time"] = dict(
        hour_x=round(x0), minute_x=round(x0 + 2 * tm["cell_w"] + tm["colon_w"]),
        colon_x=round(x0 + 2 * tm["cell_w"]), y=round(img_y),
        # no condition text (no weather slot): centred in what the band has left
        y_alone=round((((row_cy + gs / 2) + K.BAND_IN[1]) / 2 if K.GLANCE_MODE == "row" else K.MID) - tm["ink_mid"]),
        y_aod=round(K.MID - tm["ink_mid"]),       # always-on: the time is alone in the band
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
    L["edit_metrics"] = K.EDIT_METRICS
    L["fixed_slots"] = {str(k): v for k, v in K.FIXED_SLOTS.items()}
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
    for theme in THEME_NAMES:
        for r in L.get("rules") or []:
            save(rule_image(RULE_PTS[r["src"]], theme, r["x"], r["y"]), f"rule/{theme}_{r['src']}.png")
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
    make_rot_assets()
    L = build_layout(tm, bg)
    make_edit_assets(L)
    write_layout(L)
    return L
