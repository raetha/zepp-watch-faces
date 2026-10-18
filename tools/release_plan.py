#!/usr/bin/env python3
"""Work out which faces need a release, and check every face's changelog.

A face is released when its app.json version has no matching git tag
(`<face>-v<version>`). Faces containing a DRAFT file are skipped entirely. Every face's current version must have a CHANGELOG.md
section, so a version bump without notes fails CI (also on pull requests).

  python3 tools/release_plan.py            # print the plan
  python3 tools/release_plan.py --github   # also write `releases=<json>` to $GITHUB_OUTPUT
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from changelog import section  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
tags = set(subprocess.run(["git", "tag", "-l"], capture_output=True, text=True, cwd=REPO).stdout.split())
plan, problems = [], []
for app in sorted((REPO / "faces").glob("*/app.json")):
    face = app.parent.name
    if (app.parent / "DRAFT").exists():
        print(f"{face}: draft, not released")
        continue
    meta = json.loads(app.read_text())["app"]
    version = meta["version"]["name"]
    tag = f"{face}-v{version}"
    if section(face, version) is None:
        problems.append(f"faces/{face}/CHANGELOG.md needs a '## [{version}]' section (app.json version)")
    if tag not in tags:
        plan.append({"face": face, "version": version, "tag": tag, "title": f"{meta['appName']} {version}"})
    print(f"{face}: version {version} -> {'RELEASE ' + tag if tag not in tags else 'already released'}")

if problems:
    print("\n".join(problems), file=sys.stderr)
    sys.exit(1)
if "--github" in sys.argv and os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"releases={json.dumps(plan)}\n")
