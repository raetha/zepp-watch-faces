#!/usr/bin/env python3
"""Make a side-by-side test build of a face: faces/<face>-dev/ with its own app ID.

The copy sits next to the original (so relative imports of ../../../lib keep working),
installs alongside the released face as "<Name> DEV", and carries a dev version.

  python3 tools/make_dev_variant.py <face> <build-number> [<short-sha>]
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEV_APPID_OFFSET = 1_000_000          # release IDs are 8.6M-9.0M, so dev IDs never collide

face, build = sys.argv[1], int(sys.argv[2])
sha = sys.argv[3] if len(sys.argv) > 3 else ""
src, dst = REPO / "faces" / face, REPO / "faces" / f"{face}-dev"
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns("dist", "screenshots", "__pycache__", "DRAFT"))
app = json.loads((dst / "app.json").read_text())
meta = app["app"]
base_version = meta["version"]["name"]
meta["appId"] += DEV_APPID_OFFSET
meta["appName"] = f"{meta['appName']} DEV"
meta["version"] = {"code": build, "name": f"{base_version}-dev.{build}"}
meta["description"] = f"Test build {build} {sha}".strip()
for lang in app.get("i18n", {}).values():
    lang["appName"] = meta["appName"]
(dst / "app.json").write_text(json.dumps(app, indent=2) + "\n")
print(f"{dst.relative_to(REPO)}: {meta['appName']} {meta['version']['name']} (appId {meta['appId']})")
