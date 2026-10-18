#!/usr/bin/env python3
"""Assemble the GitHub Pages install site from built faces.

Expects site/<face>/<face>.zpk (the latest release of each face, downloaded by CI)
and optionally site/<face>/version.txt, then adds each face's QR code and preview
plus an index page.   python3 tools/build_site.py site
"""
import html
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
cards = []
for face_dir in sorted((REPO / "faces").iterdir()):
    app = face_dir / "app.json"
    if not app.exists() or not (site / face_dir.name / f"{face_dir.name}.zpk").exists():
        continue
    name = face_dir.name
    meta = json.loads(app.read_text())["app"]
    out = site / name
    version_file = out / "version.txt"
    version = version_file.read_text().strip() if version_file.exists() else meta["version"]["name"]
    shutil.copy(face_dir / "docs" / "install-qr.png", out / "install-qr.png")
    shutil.copy(face_dir / "screenshots" / "day.png", out / "preview.png")
    cards.append(f'''
  <section>
    <h2>{html.escape(meta["appName"]).upper()}</h2>
    <p class="ver">v{html.escape(version)}</p>
    <div class="row">
      <img class="face" src="{name}/preview.png" alt="{html.escape(meta["appName"])} preview">
      <img class="qr" src="{name}/install-qr.png" alt="Install QR code for {html.escape(meta["appName"])}">
    </div>
    <p><a href="{name}/{name}.zpk">Download {name}.zpk</a> ·
       <a href="https://github.com/raetha/zepp-watch-faces/tree/main/faces/{name}">Details</a></p>
  </section>''')

(site / "index.html").write_text(f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zepp watch faces</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin: 0; font-family: system-ui, sans-serif; background: #0b1220; color: #e8ecf2; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 32px 16px 48px; text-align: center; }}
  h1 {{ font-weight: 600; }}
  h2 {{ margin-bottom: 0; letter-spacing: .06em; color: #d6ac60; }}
  .ver {{ margin-top: 4px; color: #8a96a6; }}
  section {{ border-top: 1px solid #1d2a40; padding-top: 24px; margin-top: 24px; }}
  .row {{ display: flex; flex-wrap: wrap; gap: 24px; justify-content: center; align-items: center; }}
  img.face {{ width: 240px; max-width: 80vw; border-radius: 50%; }}
  img.qr {{ width: 200px; max-width: 70vw; background: #fff; padding: 8px; border-radius: 8px; }}
  ol {{ text-align: left; display: inline-block; line-height: 1.6; }}
  a {{ color: #7fd1ff; }}
</style>
</head>
<body>
<main>
  <h1>Zepp watch faces</h1>
  <ol>
    <li>In the Zepp app, turn on Developer Mode: Profile → Settings → About, tap the Zepp logo 7 times.</li>
    <li>Profile → your watch → Developer Mode → tap the scan icon (top right).</li>
    <li>Scan a face's QR code and confirm the install.</li>
  </ol>
  {"".join(cards)}
  <p style="margin-top:40px"><a href="https://github.com/raetha/zepp-watch-faces">Source on GitHub</a></p>
</main>
</body>
</html>
''')
print(f"site ready with {len(cards)} face(s)")
