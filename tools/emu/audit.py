#!/usr/bin/env python3
"""Measure spacing and centring on an emulator screenshot of Sextant, against its layout.

  python3 tools/emu/audit.py faces/sextant shot.png

For each complication: the icon drawing's and the value's horizontal centre relative to
the slot centre, and the visible gap between them. Then the battery block, the date stack,
the status-icon row and the condition text. Pixel threshold based, so +-1px is noise.
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

face, shot = Path(sys.argv[1]), sys.argv[2]
src = (face / "watchface" / "layout.generated.js").read_text()
L = json.loads(src[src.index("{"):src.rindex("}") + 1])
rgb = np.array(Image.open(shot).convert("RGB")).astype(int)
lum = rgb.mean(axis=2)


def ink(x0, y0, x1, y1, thr=50, white=False):
    x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
    r = (rgb[y0:y1, x0:x1].min(axis=2) > 150) if white else (lum[y0:y1, x0:x1] > thr)
    ys, xs = np.nonzero(r)
    if not len(ys):
        return None
    return x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1


names = ["TL", "TR", "BL", "BM", "BR", "TM"]
print("slot  icon dx  value dx  gap   (dx = drawn centre - slot centre)")
for n, sl in zip(names, L["slots"]):
    ic, v, cx = sl["icon"], sl["value"], sl["cx"]
    ib = ink(ic["x"], ic["y"], ic["x"] + ic["size"], ic["y"] + ic["size"])
    above = v["y"] < ic["y"]
    y0, y1 = (v["y"], ic["y"]) if above else (ic["y"] + ic["size"], v["y"] + v["h"])
    vb = ink(cx - 70, y0, cx + 70, y1, white=True)
    if not ib or not vb:
        print(f"{n:4s}  (missing)")
        continue
    gap = (ib[1] - vb[3]) if above else (vb[1] - ib[3])
    print(f"{n:4s}  {(ib[0] + ib[2]) / 2 - cx:+6.1f}  {(vb[0] + vb[2]) / 2 - cx:+7.1f}  {gap:4d}")
b = L["battery"]
bi = ink(b["icon"]["x"], b["icon"]["y"], b["icon"]["x"] + b["icon"]["size"], b["icon"]["y"] + b["icon"]["size"])
bt = ink(b["text"]["x"], bi[3] + 1, b["text"]["x"] + b["text"]["w"], b["text"]["y"] + b["text"]["h"], white=True)
bcx = b["text"]["x"] + b["text"]["w"] / 2
print(f"battery  icon dx {(bi[0] + bi[2]) / 2 - bcx:+.1f}  text dx {(bt[0] + bt[2]) / 2 - bcx:+.1f}  gap {bt[1] - bi[3]}  "
      f"block centre y {(bi[1] + bt[3]) / 2:.1f} (band middle 240)")
d = L["date"]
dcx = d["day"]["x"] + d["day"]["w"] / 2
x0, x1 = int(dcx - 36), int(dcx + 36)
y0, y1 = int(d["dow"]["y"]) + 4, int(d["month"]["y"] + d["month"]["h"]) - 4
on = (lum[y0:y1, x0:x1] > 60).any(axis=1)
runs, start = [], None
for i, v in enumerate(list(on) + [False]):
    if v and start is None:
        start = i
    elif not v and start is not None:
        runs.append((y0 + start, y0 + i)); start = None
lines = []
for ra, rb in runs:
    cols = np.nonzero((lum[ra:rb, x0:x1] > 60).any(axis=0))[0]
    lines.append((x0 + cols.min(), ra, x0 + cols.max() + 1, rb))
print("date     line dx " + " ".join(f"{(r[0] + r[2]) / 2 - dcx:+.1f}" for r in lines)
      + "  heights " + " ".join(str(r[3] - r[1]) for r in lines)
      + "  gaps " + " ".join(str(lines[i + 1][1] - lines[i][3]) for i in range(len(lines) - 1))
      + f"  block centre y {(lines[0][1] + lines[-1][3]) / 2:.1f}")
g = L["glances"]
gx0, gx1 = min(e["x"] for e in g), max(e["x"] for e in g) + 22
print(f"glances  row centre x {(gx0 + gx1) / 2:.1f} (screen 240)")
dimg = L.get("desc_img")
if dimg:
    db = ink(dimg["x"], dimg["y"], dimg["x"] + dimg["w"], dimg["y"] + dimg["h"], thr=80)
    if db:
        print(f"condition text centre x {(db[0] + db[2]) / 2:.1f}")
