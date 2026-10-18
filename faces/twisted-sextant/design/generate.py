#!/usr/bin/env python3
"""Regenerate Twisted Sextant's assets and layout with Sextant's generator.

Twisted Sextant shares Sextant's design code (faces/sextant/design) and face code
(faces/sextant/watchface/sextant.js). Only the overrides in design/variant.json differ:
corner values turned along their gauges, editable slots limited to the metrics the
face can read (so can turn), and weather fixed at the top.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

FACE = Path(__file__).resolve().parents[1]
SEXTANT = FACE.parent / "sextant"
variant = {k: v for k, v in json.loads((FACE / "design" / "variant.json").read_text()).items() if not k.startswith("_")}
extra = json.loads(os.environ.get("SEXTANT_OVERRIDES", "{}"))   # mock-ups can still layer overrides on top
env = {**os.environ, "SEXTANT_FACE_DIR": str(FACE), "SEXTANT_OVERRIDES": json.dumps({**variant, **extra})}
out = subprocess.run([sys.executable, str(SEXTANT / "design" / "generate.py")], env=env, check=True,
                     capture_output=True, text=True).stdout
print(out.replace("sextant:", "twisted-sextant:", 1), end="")
