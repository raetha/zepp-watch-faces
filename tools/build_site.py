#!/usr/bin/env python3
"""Assemble the GitHub Pages install site from built faces.

Expects site/<face>/<face>.zpk (the latest release of each face, downloaded by CI)
and optionally site/<face>/version.txt, then adds each face's preview and an index page.
The page points people to the stores (tools/stores.py); the QR code and .zpk stay
available in a smaller "sideload" part of each card.   python3 tools/build_site.py site
"""
import html
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from stores import AMAZFITWATCHFACES  # noqa: E402

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
    app_name = html.escape(meta["appName"])
    awf = (f'<li><a href="{AMAZFITWATCHFACES[name]}">{app_name} on amazfitwatchfaces.com</a></li>'
           if name in AMAZFITWATCHFACES else "")
    cards.append(f'''
  <section>
    <h2>{app_name.upper()}</h2>
    <p class="ver">v{html.escape(version)}</p>
    <img class="face" src="{name}/preview.png" alt="{app_name} preview">
    <ul class="stores">
      <li>Zepp store: in the Zepp app, search for “{app_name}” in your watch’s watch face store</li>
      {awf}
    </ul>
    <p><a href="https://github.com/raetha/zepp-watch-faces/tree/main/faces/{name}">Details</a></p>
    <details>
      <summary>Sideload instead (Developer Mode)</summary>
      <img class="qr" src="{name}/install-qr.png" alt="Install QR code for {app_name}">
      <p><a href="{name}/{name}.zpk">Download {name}.zpk</a></p>
    </details>
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
  img.face {{ width: 240px; max-width: 80vw; border-radius: 50%; }}
  img.qr {{ width: 160px; max-width: 60vw; background: #fff; padding: 8px; border-radius: 8px; margin-top: 12px; }}
  ul.stores {{ list-style: none; padding: 0; line-height: 1.8; }}
  details {{ margin-top: 12px; color: #8a96a6; }}
  summary {{ cursor: pointer; }}
  .note {{ max-width: 520px; margin: 8px auto; color: #8a96a6; line-height: 1.5; }}
  a {{ color: #7fd1ff; }}
</style>
</head>
<body>
<main>
  <h1>Zepp watch faces</h1>
  <p class="note">Install from the Zepp store or amazfitwatchfaces.com.</p>
  <p class="note">Sideloading is for testing or watches the stores don't offer. In the Zepp app, turn on Developer Mode (Profile → Settings → About, tap the Zepp logo 7 times), then Profile → your watch → Developer Mode → scan. A sideloaded face installs and works, but the Zepp app doesn't list it under Developer Mode, and it doesn't get store updates.</p>
  {"".join(cards)}
  <p style="margin-top:40px"><a href="https://github.com/raetha/zepp-watch-faces">Source on GitHub</a></p>
</main>
</body>
</html>
''')
print(f"site ready with {len(cards)} face(s)")
