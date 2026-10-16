#!/usr/bin/env python3
"""Regenerate assets for every face (or the faces named on the command line).

Each face owns its generator at faces/<face>/design/generate.py.
  python3 tools/generate.py [face ...]
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
faces = sys.argv[1:] or sorted(p.name for p in (REPO / "faces").iterdir() if (p / "design" / "generate.py").exists())
for face in faces:
    subprocess.run([sys.executable, str(REPO / "faces" / face / "design" / "generate.py")], check=True)
