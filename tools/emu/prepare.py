#!/usr/bin/env python3
"""Make an emulator install package for a face: its device.zip with the original PNGs.

`zeus build` converts images to the watch's own compressed format, which the QEMU
emulator can't decode (every image fails to load). The emulator shows plain PNGs, so
we swap the face's source assets back in. Layout and code are unchanged.

  python3 tools/emu/prepare.py faces/<face> out.zip [--device-source N]
"""
import argparse
import io
import json
import zipfile
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("face", type=Path)
ap.add_argument("out", type=Path)
ap.add_argument("--device-source", type=int, default=9568512)   # Amazfit Balance 2 (the emulated watch)
a = ap.parse_args()

zabs = sorted((a.face / "dist").glob("*.zab"))
if len(zabs) != 1:
    raise SystemExit(f"expected one .zab in {a.face}/dist (run zeus build), found {len(zabs)}")
device = None
with zipfile.ZipFile(zabs[0]) as zab:
    for name in zab.namelist():
        if not name.endswith(".zpk"):
            continue
        with zipfile.ZipFile(io.BytesIO(zab.read(name))) as zpk:
            d = zpk.read("device.zip")
        with zipfile.ZipFile(io.BytesIO(d)) as dz:
            if a.device_source in [p.get("deviceSource") for p in json.loads(dz.read("app.json"))["platforms"]]:
                device = d
                break
if device is None:
    raise SystemExit(f"no package targets deviceSource {a.device_source}")

src_assets = a.face / "assets" / "common.r"
with zipfile.ZipFile(io.BytesIO(device)) as dz, zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as out:
    for info in dz.infolist():
        if info.filename.startswith("assets/"):
            continue
        out.writestr(info, dz.read(info))
    for f in sorted(src_assets.rglob("*")):
        if f.is_file():
            out.write(f, "assets/" + f.relative_to(src_assets).as_posix())
    app_id = json.loads(dz.read("app.json"))["app"]["appId"]
print(app_id)
