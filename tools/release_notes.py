#!/usr/bin/env python3
"""Release notes for one face: its changelog section plus install instructions.

  python3 tools/release_notes.py <face> <version> > notes.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from changelog import section  # noqa: E402

face, version = sys.argv[1], sys.argv[2]
body = section(face, version)
if body is None:
    sys.exit(f"no changelog section for {face} {version}")
raw = "https://raw.githubusercontent.com/raetha/zepp-watch-faces/main"
print(f"""{body}

---

**Install:** in the Zepp app, turn on Developer Mode (Profile → Settings → About, tap the logo 7 times), then Profile → your watch → Developer Mode → scan:

<img src="{raw}/faces/{face}/docs/install-qr.png" width="180" alt="Install QR code">

Or download `{face}-{version}.zpk` below. More details: [faces/{face}](https://github.com/raetha/zepp-watch-faces/tree/main/faces/{face}) · [install page](https://raetha.github.io/zepp-watch-faces/)""")
