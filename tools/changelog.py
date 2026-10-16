#!/usr/bin/env python3
"""Read a face's CHANGELOG.md.

  python3 tools/changelog.py <face> <version>      # print that version's section
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def section(face, version):
    path = REPO / "faces" / face / "CHANGELOG.md"
    if not path.exists():
        return None
    text = path.read_text()
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else None


if __name__ == "__main__":
    body = section(sys.argv[1], sys.argv[2])
    if body is None:
        sys.exit(f"faces/{sys.argv[1]}/CHANGELOG.md has no section for [{sys.argv[2]}]")
    print(body)
