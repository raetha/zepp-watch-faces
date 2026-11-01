#!/usr/bin/env python3
"""Make a side-by-side test build of a face: faces/<face>-dev/ with its own app ID.

The app ID comes from DEV_APPIDS: a "<Name> DEV" app registered in the Zepp Console, which
the preview upload needs (docs/development.md -> "Test builds"). A face with no entry yet
falls back to its release ID + 1,000,000, which installs from our own .zpk but never shows
up under the Zepp app's Developer Mode.

The copy sits next to the original (so relative imports of ../../../lib keep working),
installs alongside the released face as "<Name> DEV", and carries a dev version.

  python3 tools/make_dev_variant.py <face> <build-number> [<short-sha>]
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# face -> app ID of its "<Name> DEV" app in the Zepp Console (register one per face)
DEV_APPIDS = {
    "sextant": 1134218,          # "Sextant DEV"
    "twisted-sextant": 1134219,  # "Twisted Sextant DEV"
}
DEV_APPID_OFFSET = 1_000_000          # fallback only, for faces without a registered DEV app

face, build = sys.argv[1], int(sys.argv[2])
sha = sys.argv[3] if len(sys.argv) > 3 else ""
src, dst = REPO / "faces" / face, REPO / "faces" / f"{face}-dev"
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns("dist", "screenshots", "__pycache__", "DRAFT"))
app = json.loads((dst / "app.json").read_text())
meta = app["app"]
base_version = meta["version"]["name"]
if face in DEV_APPIDS:
    meta["appId"] = DEV_APPIDS[face]
else:
    meta["appId"] += DEV_APPID_OFFSET
    print(f"{face}: no registered DEV app ID in DEV_APPIDS, using release ID + {DEV_APPID_OFFSET:,}")
meta["appName"] = f"{meta['appName']} DEV"
meta["version"] = {"code": build, "name": f"{base_version}-dev.{build}"}
meta["description"] = f"Test build {build} {sha}".strip()
for lang in app.get("i18n", {}).values():
    lang["appName"] = meta["appName"]
(dst / "app.json").write_text(json.dumps(app, indent=2) + "\n")
print(f"{dst.relative_to(REPO)}: {meta['appName']} {meta['version']['name']} (appId {meta['appId']})")
