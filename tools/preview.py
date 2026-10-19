#!/usr/bin/env python3
"""Render a PNG preview from the harness's widget dump (what the code actually builds).

  python3 tools/preview.py faces/<face> widgets.json scenario.json out.png [--aod|--edit]

Text placement follows the same single-line model the layout generator assumes
(line box = ascender + descender, centred in the widget box); see
docs/development.md for how to calibrate it on a real watch.
"""
import json
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ASSETS = None          # set from the face directory argument
S = 3


def rgb(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def font_metrics(path):
    f = TTFont(path)
    upm = f["head"].unitsPerEm
    return f["hhea"].ascent / upm, -f["hhea"].descent / upm


def asset(rel):
    return Image.open(ASSETS / rel).convert("RGBA")


def paste(canvas, rel, x, y):
    im = asset(rel)
    im = im.resize((im.width * S, im.height * S), Image.LANCZOS)
    canvas.alpha_composite(im, (int(round(x * S)), int(round(y * S))))


def paste_turned(canvas, p):
    """An IMG with `angle`: the image sits at (pos_x, pos_y) in a w x h box and turns about
    (center_x, center_y), clockwise for positive angles, as the firmware does."""
    im = asset(p["src"])
    w, h = p.get("w", im.width), p.get("h", im.height)
    box = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    box.alpha_composite(im.resize((im.width * S, im.height * S), Image.LANCZOS),
                        (int(p.get("pos_x", 0) * S), int(p.get("pos_y", 0) * S)))
    c = (p.get("center_x", w / 2) * S, p.get("center_y", h / 2) * S)
    box = box.rotate(-p["angle"], resample=Image.BICUBIC, center=c)
    canvas.alpha_composite(box, (int(round(p.get("x", 0) * S)), int(round(p.get("y", 0) * S))))


def draw_text(canvas, p, text):
    if not text:
        return
    font_path = ASSETS / p["font"]
    size = p["text_size"]
    asc, desc = font_metrics(font_path)
    f = ImageFont.truetype(str(font_path), int(round(size * S)))
    line_h = (asc + desc) * size
    baseline = p["y"] + (p["h"] - line_h) / 2 + asc * size
    d = ImageDraw.Draw(canvas)
    width = f.getlength(text) / S
    align = p.get("align_h")
    if align == 3:            # LEFT
        x = p["x"]
    elif align == 4:          # RIGHT
        x = p["x"] + p["w"] - width
    else:                     # CENTER_H
        x = p["x"] + (p["w"] - width) / 2
    d.text((x * S, baseline * S), text, font=f, fill=rgb(p.get("color", 0xFFFFFF)), anchor="ls")


def draw_arc(canvas, p, level):
    if level <= 0:
        return
    # the firmware truncates arc angles to whole degrees (and the filled end too)
    a0, a1 = math.floor(p["start_angle"]), math.floor(p["end_angle"])
    end = a0 + math.trunc((a1 - a0) * level / 100)
    lo, hi = sorted((a0, end))
    r, w = p["radius"], p["line_width"]
    cx, cy = p["center_x"], p["center_y"]
    d = ImageDraw.Draw(canvas)
    box = [(cx - r - w / 2) * S, (cy - r - w / 2) * S, (cx + r + w / 2) * S, (cy + r + w / 2) * S]
    d.arc(box, lo - 90, hi - 90, fill=rgb(p["color"]), width=int(w * S))


def draw_edit(canvas, dump, scenario):
    """Edit-mode look, as the firmware draws it: only ONLY_EDIT widgets (drawn by render)
    plus each edit group's current option preview and frame, first group selected with its tip."""
    picks = list(scenario.get("edit", []))
    groups = [w for w in dump["widgets"] if w["type"] == "WATCHFACE_EDIT_GROUP"]
    for i, w in enumerate(groups):
        p = w["props"]
        pick = picks[i] if i < len(picks) else None
        types = p.get("optional_types", [])
        opt = next((t for t in types if t.get("data", {}).get("id") == pick), None) or \
            next((t for t in types if t["type"] == p.get("default_type")), None)
        if opt and opt.get("preview"):
            paste(canvas, opt["preview"], p["x"], p["y"])
        paste(canvas, p["select_image"] if i == 0 else p["un_select_image"], p["x"], p["y"])
    if groups and groups[0]["props"].get("tips_BG"):
        p = groups[0]["props"]
        pick = picks[0] if picks else None
        types = p.get("optional_types", [])
        opt = next((t for t in types if t.get("data", {}).get("id") == pick), None) or \
            next((t for t in types if t["type"] == p.get("default_type")), None)
        tx, ty = p["x"] + p.get("tips_x", 0), p["y"] + p.get("tips_y", 0)
        paste(canvas, p["tips_BG"], tx, ty)
        name = (opt.get("title_en") or opt.get("title") or "") if opt else ""
        if name:
            tip = asset(p["tips_BG"])
            draw_text(canvas, {"x": tx, "y": ty, "w": tip.width, "h": tip.height, "text_size": 22,
                               "color": 0x1A1A1A, "align_h": 2, "font": "fonts/RobotoCondensed-Regular.ttf"}, name)


def render(dump, scenario, aod=False, edit=False):
    level_wanted = 2 if aod else 4 if edit else 1
    canvas = Image.new("RGBA", (480 * S, 480 * S), (0, 0, 0, 255))
    bound = scenario.get("bound", {})
    glances = set(scenario.get("glances", []))
    T = scenario["sensors"]["TIME"]
    for w in dump["widgets"]:
        p = w["props"]
        if w["type"] == "WATCHFACE_EDIT_GROUP" or not w["visible"]:
            continue
        if p.get("show_level", 1) != level_wanted:
            continue
        t = w["type"]
        if t == "IMG" and p.get("src") and p.get("angle"):
            paste_turned(canvas, p)
        elif t == "IMG" and p.get("src"):
            paste(canvas, p["src"], p.get("x", 0), p.get("y", 0))
        elif t == "IMG_STATUS":
            name = Path(p["src"]).stem
            if name in glances:
                paste(canvas, p["src"], p["x"], p["y"])
        elif t == "IMG_LEVEL":
            if p.get("type") == "WEATHER_CURRENT":
                i = scenario["sensors"].get("WEATHER", {}).get("curAirIconIndex", 25)
            else:
                i = bound.get(p.get("type"), {}).get("level", 0)
            arr = p["image_array"]
            paste(canvas, arr[max(0, min(len(arr) - 1, int(i)))], p.get("x", 0), p.get("y", 0))
        elif t == "FILL_RECT":
            c = p.get("color", 0)
            rgb = ((c >> 16) & 255, (c >> 8) & 255, c & 255, 255)
            x, y, w_, h = (p.get(k, 0) * S for k in ("x", "y", "w", "h"))
            if w_ > 0 and h > 0:
                ImageDraw.Draw(canvas).rounded_rectangle([x, y, x + w_ - 1, y + h - 1], radius=p.get("radius", 0) * S, fill=rgb)
        elif t == "ARC_PROGRESS":
            lvl = bound.get(p["type"], {}).get("level", 0) if p.get("type") else p.get("level", 0)
            draw_arc(canvas, p, lvl)
        elif t == "TEXT":
            draw_text(canvas, p, p.get("text", ""))
        elif t == "TEXT_FONT":
            draw_text(canvas, p, bound.get(p.get("type"), {}).get("value", "--"))
        elif t == "IMG_TIME":
            if "hour_array" in p:
                h = T["hour"]
                if scenario.get("is12h"):
                    h = h % 12 or 12
                digits, x, y, arr = f"{h:02d}", p["hour_startX"], p["hour_startY"], p["hour_array"]
            else:
                digits, x, y, arr = f"{T['minute']:02d}", p["minute_startX"], p["minute_startY"], p["minute_array"]
            for ch in digits:
                rel = arr[int(ch)]
                paste(canvas, rel, x, y)
                x += asset(rel).width
    if edit:
        draw_edit(canvas, dump, scenario)
    out = canvas.resize((480, 480), Image.LANCZOS)
    mask = Image.new("L", (480, 480), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 479, 479], fill=255)
    final = Image.new("RGB", (480, 480), (0, 0, 0))
    final.paste(out, (0, 0), mask)
    return final


if __name__ == "__main__":
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    ASSETS = Path(pos[0]).resolve() / "assets" / "common.r"
    dump = json.loads(Path(pos[1]).read_text())
    scen = json.loads(Path(pos[2]).read_text())
    render(dump, scen, aod="--aod" in sys.argv, edit="--edit" in sys.argv).save(pos[3])
