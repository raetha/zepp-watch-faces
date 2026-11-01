#!/usr/bin/env python3
"""Make the install QR code for the Zepp app's developer-mode scanner.

The Zepp app accepts `zpkd1://<host>/<path>.zpk` and downloads the package over
HTTPS. The CI workflow publishes the package to GitHub Pages at a fixed URL, so
the QR code never changes and is committed to the repo.

  python3 tools/make_qr.py <face> [url]
"""
import sys
from pathlib import Path
from zepp_devkit.qr import make

ROOT = Path(__file__).resolve().parents[1]
PAGES = "raetha.github.io/zepp-watch-faces"

face = sys.argv[1]
url = sys.argv[2] if len(sys.argv) > 2 else f"zpkd1://{PAGES}/{face}/{face}.zpk"
out = make(ROOT / "faces" / face / "docs" / "install-qr.png", url, "#14223A")
print(f"{out}  ->  {url}")
