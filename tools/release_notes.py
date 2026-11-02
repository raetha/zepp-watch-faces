#!/usr/bin/env python3
"""Release notes for one face: its changelog section plus install instructions (zepp-devkit's
notes(), with the faces' install text).

  python3 tools/release_notes.py <face> <version> > notes.md
"""
import sys
from pathlib import Path

from zepp_devkit.release import notes

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stores import store_lines_md  # noqa: E402
import json

face, version = sys.argv[1], sys.argv[2]
raw = "https://raw.githubusercontent.com/raetha/zepp-watch-faces/main"
app_name = json.loads((Path(__file__).resolve().parents[1] / "faces" / face / "app.json").read_text())["app"]["appName"]
print(notes(Path(__file__).resolve().parents[1] / "faces" / face / "CHANGELOG.md", version, f"""**Install:**

{store_lines_md(face, app_name)}

<details><summary>Sideload instead (Developer Mode)</summary>

In the Zepp app, turn on Developer Mode (Profile → Settings → About, tap the logo 7 times), then Profile → your watch → Developer Mode → scan. A sideloaded face doesn't get store updates.

<img src="{raw}/faces/{face}/docs/install-qr.png" width="160" alt="Install QR code">

Or download `{face}-{version}.zpk` below.
</details>

More details: [faces/{face}](https://github.com/raetha/zepp-watch-faces/tree/main/faces/{face}) · [install page](https://raetha.github.io/zepp-watch-faces/)"""))
