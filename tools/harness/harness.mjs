#!/usr/bin/env node
/**
 * Offline test harness: runs watchface/index.js against stubbed Zepp OS globals
 * (hmUI / hmSensor / hmSetting / WatchFace), then dumps the live widget tree as JSON.
 *
 * It catches runtime errors and missing assets without a watch, and its output
 * drives tools/preview.py, which renders README screenshots from the real code.
 *
 *   node tools/harness/harness.mjs faces/<face> faces/<face>/scenarios/day.json > widgets.json
 */
import { build } from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const FACE = path.resolve(REPO, process.argv[2]);
const ASSETS = path.join(FACE, 'assets/common.r');
const scenario = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));

const enumOf = (names) => Object.fromEntries(names.map((n, i) => [n, i + 1]));
const WIDGET = enumOf(['IMG', 'TEXT', 'TEXT_FONT', 'ARC_PROGRESS', 'IMG_TIME', 'IMG_STATUS', 'IMG_LEVEL', 'WATCHFACE_EDIT_GROUP', 'WIDGET_DELEGATE', 'GROUP']);
const WIDGET_NAME = Object.fromEntries(Object.entries(WIDGET).map(([k, v]) => [v, k]));
const PROP = enumOf(['TEXT', 'SRC', 'VISIBLE', 'MORE', 'CURRENT_TYPE', 'COLOR']);
const DATA_TYPES = ['STEP', 'CAL', 'HEART', 'DISTANCE', 'FLOOR', 'STAND', 'FAT_BURNING', 'SPO2', 'STRESS', 'UVI',
  'HUMIDITY', 'AQI', 'PAI_WEEKLY', 'WEATHER_CURRENT', 'BATTERY'];

const widgets = [];
const errors = [];
let editCounter = 0;

function makeWidget(type, props) {
  const w = { id: widgets.length, type: WIDGET_NAME[type], props: { ...props }, alive: true, visible: true };
  widgets.push(w);
  for (const key of ['src']) checkAsset(w.props[key], w);
  for (const key of ['hour_array', 'minute_array', 'image_array']) (w.props[key] || []).forEach((p) => checkAsset(p, w));
  for (const key of ['select_image', 'un_select_image', 'tips_BG']) checkAsset(w.props[key], w);
  (w.props.optional_types || []).forEach((t) => checkAsset(t.preview, w));
  if (w.props.font) checkAsset(w.props.font, w);
  return {
    setProperty(prop, value) {
      if (prop === PROP.TEXT) w.props.text = value;
      else if (prop === PROP.SRC) { w.props.src = value; checkAsset(value, w); }
      else if (prop === PROP.VISIBLE) w.visible = !!value;
      else if (prop === PROP.MORE) Object.assign(w.props, value);
      else if (prop === PROP.COLOR) w.props.color = value;
      else errors.push(`unknown setProperty ${prop}`);
    },
    getProperty(prop) {
      if (prop === PROP.CURRENT_TYPE) {
        const pick = (scenario.edit || [])[editCounter++];
        const types = w.props.optional_types;
        const t = types.find((x) => x.data.id === pick) || types.find((x) => x.type === w.props.default_type);
        return t.type;
      }
      return undefined;
    },
    _w: w,
  };
}

function checkAsset(rel, w) {
  if (!rel) return;
  if (!fs.existsSync(path.join(ASSETS, rel))) errors.push(`missing asset "${rel}" (widget ${w.type} #${w.id})`);
}

const S = scenario.sensors || {};
const sensorIds = enumOf(['TIME', 'BATTERY', 'STEP', 'CALORIE', 'HEART', 'DISTANCE', 'WEATHER', 'PAI', 'SLEEP']);
const sensorName = Object.fromEntries(Object.entries(sensorIds).map(([k, v]) => [v, k]));
const listeners = [];
const hmSensor = {
  id: sensorIds,
  event: enumOf(['CHANGE', 'LAST']),
  createSensor(id) {
    const name = sensorName[id];
    const data = S[name] || {};
    const obj = {
      ...data,
      event: { MINUTEEND: 100 },
      addEventListener(ev, fn) { listeners.push({ name, ev, fn }); },
      removeEventListener() {},
    };
    if (name === 'WEATHER') obj.getForecastWeather = () => data.forecast || { tideData: { count: 0, data: [] } };
    return obj;
  },
};

let watchface = null;
const context = {
  console,
  px: (v) => v,
  WatchFace: (def) => { watchface = def; },
  hmSensor,
  hmSetting: {
    getTimeFormat: () => (scenario.is12h ? 0 : 1),
    getMileageUnit: () => (scenario.imperial ? 1 : 0),
    getScreenType: () => 1,
    screen_type: { WATCHFACE: 1, AOD: 2 },
  },
  hmUI: {
    widget: WIDGET,
    prop: PROP,
    align: enumOf(['TOP', 'BOTTOM', 'LEFT', 'RIGHT', 'CENTER_H', 'CENTER_V']),
    show_level: { ONLY_NORMAL: 1, ONLY_AOD: 2, ONLY_EDIT: 4 },
    system_status: enumOf(['DISCONNECT', 'DISTURB', 'CLOCK', 'LOCK']),
    data_type: enumOf(DATA_TYPES),
    createWidget: makeWidget,
    deleteWidget(handle) { handle._w.alive = false; },
  },
};
context.globalThis = context;

const out = await build({
  entryPoints: [path.join(FACE, 'watchface/index.js')],
  bundle: true, format: 'iife', write: false, target: 'es2019', logLevel: 'silent',
});
vm.createContext(context);
vm.runInContext(out.outputFiles[0].text, context, { filename: 'watchface.js' });
if (!watchface) throw new Error('WatchFace() was never called');
watchface.build();
// simulate a later minute tick so theme switching + updates run again
for (const l of listeners.filter((x) => x.name === 'TIME')) l.fn();

const dataTypeName = Object.fromEntries(Object.entries(context.hmUI.data_type).map(([k, v]) => [v, k]));
const live = widgets.filter((w) => w.alive && w.type !== 'WIDGET_DELEGATE').map((w) => ({
  ...w, props: { ...w.props, type: w.props.type && w.type !== 'WATCHFACE_EDIT_GROUP' ? dataTypeName[w.props.type] : w.props.type },
}));
process.stdout.write(JSON.stringify({ errors, widgets: live }, null, 1));
if (errors.length) {
  console.error(errors.join('\n'));
  process.exitCode = 1;
}
