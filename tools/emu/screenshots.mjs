#!/usr/bin/env node
/**
 * Take a face's README screenshots on the real firmware (the QEMU emulator), following
 * faces/<face>/emu-shots.json. Writes faces/<face>/screenshots/*.png (round, on black)
 * and refreshes the face's icon.png and cover.png from day.png.
 *
 *   node tools/emu/screenshots.mjs <face> [--run N]   (npm run screenshots -- <face>); --run: only that run
 *
 * Needs `node tools/emu/emu.mjs setup` and a base watch state with the always-on screen
 * turned on (`emu.mjs start`, `enable-aod`, `save-base`); see docs/development.md.
 *
 * Steps: {set: {...}} values on top of the file's "values"; {shot: name};
 * {aod: name} screen off -> always-on shot -> wake; {edit: "open" | "close"};
 * {edit: "slot0".."slot4" | "theme" | "night", taps: n} cycle that edit group n options;
 * {wait: ms} (e.g. for the next minute tick: the 12/24-hour setting applies then).
 */
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const face = process.argv[2];
const onlyRun = process.argv.includes('--run') ? Number(process.argv[process.argv.indexOf('--run') + 1]) : null;
if (!face) { console.error('usage: screenshots.mjs <face>'); process.exit(1); }
const faceDir = path.join(REPO, 'faces', face);
const plan = JSON.parse(fs.readFileSync(path.join(faceDir, 'emu-shots.json'), 'utf8'));
const layoutSrc = fs.readFileSync(path.join(faceDir, 'watchface/layout.generated.js'), 'utf8');
const L = JSON.parse(layoutSrc.slice(layoutSrc.indexOf('{'), layoutSrc.lastIndexOf('}') + 1));
const shots = path.join(faceDir, 'screenshots');
const raw = path.join(REPO, 'tools/.emu/shots', face);
fs.mkdirSync(shots, { recursive: true });
fs.mkdirSync(raw, { recursive: true });

const emu = (...args) => execFileSync('node', [path.join(REPO, 'tools/emu/emu.mjs'), ...args.map(String)],
  { stdio: ['ignore', 'pipe', 'inherit'] }).toString();
const sleep = (ms) => execFileSync('sleep', [String(ms / 1000)]);
// The screen times out to the always-on view between steps; a tap on the face wakes it
// (faces here have no tap actions), then make sure we're on the face, not the app list.
const wake = () => { emu('tap', 240, 240); emu('face'); };

const centre = (box) => [Math.round(box.x + box.w / 2), Math.round(box.y + box.h / 2)];
const groups = {
  slot0: centre(L.slots[0].edit), slot1: centre(L.slots[1].edit), slot2: centre(L.slots[2].edit),
  slot3: centre(L.slots[3].edit), slot4: centre(L.slots[4].edit),
  theme: centre(L.theme_edit), night: centre(L.night_edit),
};

function shot(name) {
  const file = path.join(raw, `${name}.png`);
  emu('shot', file);
  // round crop on black, like a real watch photo
  execFileSync('python3', ['-c', `
import sys
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]).convert('RGB')
m = Image.new('L', (im.width * 4, im.height * 4), 0)
ImageDraw.Draw(m).ellipse([0, 0, m.width - 1, m.height - 1], fill=255)
out = Image.new('RGB', im.size, (0, 0, 0)); out.paste(im, (0, 0), m.resize(im.size, Image.LANCZOS)); out.save(sys.argv[2])
`, file, path.join(shots, `${name}.png`)]);
  console.log(`  ${name}.png`);
}

let selected = null;
for (const [ri, run] of plan.runs.entries()) {
  if (onlyRun !== null && ri !== onlyRun) continue;
  console.log(`boot at ${run.time}`);
  emu('reset');
  emu('start', '--time', run.time);
  emu('install', face);
  emu('set', ...Object.entries(plan.values).map(([k, v]) => `${k}=${v}`));
  for (const step of run.steps) {
    if (step.set) emu('set', ...Object.entries({ ...plan.values, ...step.set }).map(([k, v]) => `${k}=${v}`));
    else if (step.wait) sleep(step.wait);
    else if (step.shot) { if (!selected) wake(); shot(step.shot); }
    else if (step.aod) { wake(); emu('rest'); sleep(3000); shot(step.aod); wake(); }
    else if (step.edit === 'open') { wake(); emu('tap', 240, 240, 2.5); emu('tap', 240, 438); sleep(1500); selected = 'slot0'; }
    else if (step.edit === 'close') { emu('key', 'ret'); sleep(2500); selected = null; }
    else if (step.edit) {
      const [x, y] = groups[step.edit];
      if (selected !== step.edit) { emu('tap', x, y); selected = step.edit; }
      for (let i = 0; i < (step.taps || 0); i++) emu('tap', x, y);
    } else throw new Error(`unknown step ${JSON.stringify(step)}`);
  }
  emu('stop');
}
if (onlyRun === null || onlyRun === 1) execFileSync('python3', [path.join(REPO, 'tools/make_covers.py'), faceDir], { stdio: 'inherit' });
