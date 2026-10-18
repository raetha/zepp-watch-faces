#!/usr/bin/env python3
"""Add the unlisted test-build page to the Pages site.

Expects site/dev/<face>/<face>.zpk (fresh test builds). Writes a QR code for each
and site/dev/index.html. The page is not linked from the main site and is marked
noindex; its QR codes never change, so you can bookmark the page.

  python3 tools/dev_site.py site <short-sha> <build-number>
"""
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import qrcode

REPO = Path(__file__).resolve().parents[1]
PAGES = "raetha.github.io/zepp-watch-faces"
site, sha, build = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
dev = site / "dev"
cards = []
for face_dir in sorted((dev).iterdir()) if dev.exists() else []:
    face = face_dir.name
    if not (face_dir / f"{face}.zpk").exists():
        continue
    url = f"zpkd1://{PAGES}/dev/{face}/{face}.zpk"
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="#14223A", back_color="white").save(face_dir / "install-qr.png")
    meta = json.loads((REPO / "faces" / face / "app.json").read_text())["app"]
    cards.append(f'''<section><h2>{html.escape(meta["appName"])} DEV</h2>
<p>based on {html.escape(meta["version"]["name"])} · build {html.escape(build)} · {html.escape(sha)}</p>
<img class="qr" src="{face}/install-qr.png" alt="QR code for the {html.escape(face)} test build">
<p><a href="{face}/{face}.zpk">{face}.zpk</a></p></section>''')
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
(dev / "index.html").write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Test builds</title>
<style>:root{{color-scheme:dark}}body{{margin:0;font-family:system-ui,sans-serif;background:#0b1220;color:#e8ecf2;text-align:center}}
main{{max-width:640px;margin:0 auto;padding:24px 16px}}h2{{color:#d6ac60;margin-bottom:4px}}p{{color:#9aa6b6}}
img.qr{{width:220px;max-width:70vw;background:#fff;padding:8px;border-radius:8px}}a{{color:#7fd1ff}}
section{{border-top:1px solid #1d2a40;margin-top:20px;padding-top:12px}}</style></head>
<body><main><h1>Test builds</h1>
<p>Latest push to main ({html.escape(sha)}, {stamp}). These install next to the released faces as separate "DEV" apps.
GitHub Pages can cache files for up to 10 minutes after a push.</p>
{"".join(cards)}
</main></body></html>
''')
(site / "robots.txt").write_text("User-agent: *\nDisallow: /dev/\n")
print(f"dev page with {len(cards)} build(s)")
