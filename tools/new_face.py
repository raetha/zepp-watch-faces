#!/usr/bin/env python3
"""Start a new face by copying an existing one as a template.

  python3 tools/new_face.py <new-name> [--from sextant] [--title "Display Name"]

Copies the face's code, design generator and scenarios (not its screenshots),
gives it a fresh appId and name, then you change design/config.py and the code.
"""
import argparse
import json
import random
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--from", dest="src", default="sextant")
ap.add_argument("--title")
a = ap.parse_args()

src, dst = REPO / "faces" / a.src, REPO / "faces" / a.name
if dst.exists():
    raise SystemExit(f"{dst} already exists")
shutil.copytree(src, dst, ignore=shutil.ignore_patterns("screenshots", "__pycache__", "install-qr.png"))
title = a.title or a.name.replace("-", " ").title()
app = json.loads((dst / "app.json").read_text())
used = {json.loads(p.read_text())["app"]["appId"] for p in (REPO / "faces").glob("*/app.json")}
app_id = random.randint(8_600_000, 8_999_999)
while app_id in used:
    app_id = random.randint(8_600_000, 8_999_999)
app["app"]["appId"] = app_id
app["app"]["appName"] = title
app["app"]["version"] = {"code": 1, "name": "0.1.0"}
app["app"]["description"] = f"{title} watch face. Source: https://github.com/raetha/zepp-watch-faces"
for lang in app.get("i18n", {}).values():
    lang["appName"] = title
(dst / "app.json").write_text(json.dumps(app, indent=2) + "\n")
(dst / "CHANGELOG.md").write_text(f"""# Changelog: {title}

All notable changes to the {title} watch face. Format: Keep a Changelog; versions: SemVer.
The version here must match `version.name` in `app.json`; bumping it publishes a release.

## [Unreleased]

## [0.1.0] - YYYY-MM-DD

### Added
- First release.
""")
(dst / "DRAFT").write_text("Delete this file when the face is ready for its first release.\n")
print(f"created faces/{a.name} (appId {app_id}, marked DRAFT so it is not released yet).")
print(f"Next: edit faces/{a.name}/design/, then npm run assets && npm test")
