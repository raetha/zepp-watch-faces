#!/usr/bin/env python3
"""Make a face's side-by-side test build: faces/<face>-dev/ (ignored by git), "<Name> DEV".

The faces' settings for zepp-devkit's dev-variant. The app ID comes from DEV_APPIDS: a
"<Name> DEV" app registered in the Zepp Console, which the preview upload needs
(docs/development.md -> "Test builds"). A face with no entry yet falls back to its release
ID + 1,000,000, which installs from our own .zpk but never shows up under the Zepp app's
Developer Mode. The copy sits next to the original, so relative imports of ../../../lib
keep working.

  python3 tools/make_dev_variant.py <face> <build-number> [<short-sha>]
"""
import json
import sys
from pathlib import Path

from zepp_devkit.devvariant import make_variant

REPO = Path(__file__).resolve().parents[1]
# face -> app ID of its "<Name> DEV" app in the Zepp Console (register one per face)
DEV_APPIDS = {
    "sextant": 1134218,          # "Sextant DEV"
    "twisted-sextant": 1134219,  # "Twisted Sextant DEV"
}
DEV_APPID_OFFSET = 1_000_000          # fallback only, for faces without a registered DEV app

face, build = sys.argv[1], int(sys.argv[2])
sha = sys.argv[3] if len(sys.argv) > 3 else ""
src = REPO / "faces" / face
app_id = DEV_APPIDS.get(face)
if app_id is None:
    app_id = json.loads((src / "app.json").read_text())["app"]["appId"] + DEV_APPID_OFFSET
    print(f"{face}: no registered DEV app ID in DEV_APPIDS, using release ID + {DEV_APPID_OFFSET:,}")
meta = make_variant(src, REPO / "faces" / f"{face}-dev", app_id, build, sha, ignore=["screenshots"])
print(f"faces/{face}-dev: {meta['appName']} {meta['version']['name']} (appId {meta['appId']})")
