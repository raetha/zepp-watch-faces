#!/usr/bin/env python3
"""Make the install QR code for the Zepp app's developer-mode scanner.

The Zepp app accepts `zpkd1://<host>/<path>.zpk` and downloads the package over
HTTPS. The CI workflow publishes the package to GitHub Pages at a fixed URL, so
the QR code never changes and is committed to the repo.

  python3 tools/make_qr.py <face> [url]
"""
import sys
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PAGES = "raetha.github.io/zepp-watch-faces"

face = sys.argv[1]
url = sys.argv[2] if len(sys.argv) > 2 else f"zpkd1://{PAGES}/{face}/{face}.zpk"
out = ROOT / "faces" / face / "docs" / "install-qr.png"
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=3)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color="#14223A", back_color="white").convert("RGB")
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out)
print(f"{out}  ->  {url}")
