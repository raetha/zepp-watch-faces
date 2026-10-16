#!/usr/bin/env python3
"""Write a face's assets/common.r/icon.png and cover.png from its screenshots/day.png.

  python3 tools/make_covers.py faces/<face>
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

face = Path(sys.argv[1]).resolve()
day = Image.open(face / "screenshots" / "day.png").convert("RGBA")


def round_img(img, size):
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask.resize((size, size), Image.LANCZOS))
    return out


out = face / "assets" / "common.r"
round_img(day, 324).save(out / "cover.png")      # 480x480 devices use a 324x324 preview
round_img(day, 248).save(out / "icon.png")
print(f"{face.name}: wrote cover.png and icon.png")
