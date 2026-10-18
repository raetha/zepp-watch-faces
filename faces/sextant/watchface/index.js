/**
 * Copyright (c) 2026 raetha. Licensed CC BY-NC-SA 4.0 (see faces/sextant/LICENSE).
 *
 * Sextant watch face for Zepp OS (API level 1 globals: hmUI / hmSensor / hmSetting).
 *
 * Structure
 *  - Edit groups are created once in build(): five complication slots, a theme
 *    picker (Color / Mono) and a night-mode switch (Auto / Off).
 *  - render(theme) creates every visible widget for one theme. When the theme
 *    changes (night mode turns on at sunset, off at sunrise) the rendered widgets
 *    are deleted and recreated; sensors and listeners live outside render().
 *  - All coordinates come from layout.generated.js, produced by
 *    faces/sextant/design/generate.py together with the image assets.
 */
import { LAYOUT as L } from './layout.generated';
import { METRIC_IDS, SENSOR_METRICS, BOUND_METRICS } from '../../../lib/js/metrics';
import { isNight } from '../../../lib/js/sun';
import { textWidth } from '../../../lib/js/format';

// ------------------------------------------------------------------ options
/** Time digits for the colour theme: 'color' (brass) or 'color_white'. */
const COLOR_TIME_STYLE = 'color';
/**
 * How the firmware interprets ARC_PROGRESS `radius`: true = centre of the stroke
 * (ticks keep a common outer edge either way thanks to per-tick radii).
 */
const ARC_RADIUS_IS_CENTER = true;

const WEEKDAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

// ------------------------------------------------------------------ editor options
/** Glyph image names for CORNER_ROTATE (see design/assets.py ROT_CHARS). */
const ROT_CODES = { ',': 'comma', '.': 'dot', '-': 'dash', ':': 'colon' };
for (let d = 0; d < 10; d++) ROT_CODES[String(d)] = String(d);

function editType(type, title, preview, id) {
  return { type, title_en: title, title_sc: title, title_tc: title, preview, data: { id } };
}
const SLOT_TYPES = METRIC_IDS.map((id, i) =>
  editType(100001 + i, L.metrics[id].title, `edit/preview_${id}.png`, id));
const THEME_TYPES = [
  editType(100101, 'Color', 'edit/preview_theme_color.png', 'color'),
  editType(100102, 'Mono', 'edit/preview_theme_mono.png', 'mono'),
];
const NIGHT_TYPES = [
  editType(100201, 'Night mode: auto', 'edit/preview_night_auto.png', 'auto'),
  editType(100202, 'Night mode: off', 'edit/preview_night_off.png', 'off'),
];

function px_(v) {
  return typeof px === 'function' ? px(v) : v;
}

WatchFace({
  build() {
    this.sensors = {};
    this.widgets = [];
    this.dyn = null;
    this.theme = null;

    this.timeSensor = this.sensor('TIME');
    this.batterySensor = this.sensor('BATTERY');
    this.weatherSensor = this.sensor('WEATHER');

    // Edit-mode backdrop. The firmware hides normal widgets while editing and draws edit
    // previews in creation order, so this must exist before the edit groups.
    this.editBg = hmUI.createWidget(hmUI.widget.IMG, {
      x: 0, y: 0, src: 'edit/bg_color.png', show_level: hmUI.show_level.ONLY_EDIT,
    });
    this.settings = this.buildEditGroups();
    this.subscribe();
    this.applyTheme(true);

    hmUI.createWidget(hmUI.widget.WIDGET_DELEGATE, {
      resume_call: () => {
        this.applyTheme(false);
        this.update();
      },
    });
  },

  onDestroy() {
    this.unsubscribe && this.unsubscribe();
  },

  // ---------------------------------------------------------------- sensors
  sensor(name) {
    if (!this.sensors[name]) {
      const id = hmSensor.id[name];
      this.sensors[name] = id === undefined ? null : hmSensor.createSensor(id);
    }
    return this.sensors[name];
  },

  subscribe() {
    const onMinute = () => {
      this.applyTheme(false);
      this.update();
    };
    const onChange = () => this.update();
    const subs = [];
    if (this.timeSensor && this.timeSensor.addEventListener) {
      this.timeSensor.addEventListener(this.timeSensor.event.MINUTEEND, onMinute);
      subs.push(() => this.timeSensor.removeEventListener(this.timeSensor.event.MINUTEEND, onMinute));
    }
    const watched = new Set(['BATTERY']);
    this.settings.slots.forEach((id) => {
      const def = SENSOR_METRICS[id];
      if (def && def.sensor !== 'WEATHER') watched.add(def.sensor);
    });
    watched.forEach((name) => {
      const s = this.sensor(name);
      if (!s || !s.addEventListener) return;
      const def = Object.values(SENSOR_METRICS).find((d) => d.sensor === name);
      const ev = def && def.event ? hmSensor.event[def.event] : hmSensor.event.CHANGE;
      s.addEventListener(ev, onChange);
      subs.push(() => s.removeEventListener && s.removeEventListener(ev, onChange));
    });
    this.unsubscribe = () => subs.forEach((f) => f());
  },

  // ---------------------------------------------------------------- editor
  buildEditGroups() {
    const group = (id, box, types, defaultId, tipsBelow) => {
      const def = types.find((t) => t.data.id === defaultId) || types[0];
      const g = hmUI.createWidget(hmUI.widget.WATCHFACE_EDIT_GROUP, {
        edit_id: id,
        x: px_(box.x),
        y: px_(box.y),
        w: px_(box.w),
        h: px_(box.h),
        select_image: `edit/select_${box.w}x${box.h}.png`,
        un_select_image: `edit/unselect_${box.w}x${box.h}.png`,
        default_type: def.type,
        optional_types: types,
        count: types.length,
        tips_BG: 'edit/tip.png',
        tips_x: px_(box.w / 2 - 75),
        tips_y: px_(tipsBelow ? box.h + 6 : -46),
        tips_width: px_(150),
        tips_margin: px_(6),
      });
      const current = g.getProperty(hmUI.prop.CURRENT_TYPE);
      const chosen = types.find((t) => t.type === current) || def;
      return chosen.data.id;
    };
    const slots = L.slots.map((s, i) => group(101 + i, s.edit, SLOT_TYPES, L.default_slots[i], i < 2 || i === 5));
    const theme = group(120, L.theme_edit, THEME_TYPES, 'color', false);
    const night = group(121, L.night_edit, NIGHT_TYPES, 'auto', false);
    return { slots, theme, night };
  },

  // ---------------------------------------------------------------- theme
  wantedTheme() {
    if (this.settings.night === 'auto' && isNight(this.weatherSensor, this.timeSensor)) return 'night';
    return this.settings.theme;
  },

  applyTheme(force) {
    const theme = this.wantedTheme();
    if (!force && theme === this.theme) return;
    this.theme = theme;
    this.widgets.forEach((w) => hmUI.deleteWidget(w));
    this.widgets = [];
    this.render(theme);
    this.update();
  },

  w(type, props) {
    const widget = hmUI.createWidget(type, props);
    this.widgets.push(widget);
    return widget;
  },

  text(box, extra) {
    return this.w(hmUI.widget.TEXT, {
      x: px_(box.x),
      y: px_(box.y),
      w: px_(box.w),
      h: px_(box.h),
      text: '',
      text_size: px_(box.size),
      align_h: hmUI.align.CENTER_H,
      align_v: hmUI.align.CENTER_V,
      font: L.font,
      show_level: hmUI.show_level.ONLY_NORMAL,
      ...extra,
    });
  },

  // ---------------------------------------------------------------- render
  render(theme) {
    const C = L.colors[theme];
    const NORMAL = hmUI.show_level.ONLY_NORMAL;
    const AOD = hmUI.show_level.ONLY_AOD;
    const dyn = { slots: [] };
    this.dyn = dyn;

    this.w(hmUI.widget.IMG, { x: 0, y: 0, src: C.bg, show_level: NORMAL });
    this.editBg.setProperty(hmUI.prop.SRC, `edit/bg_${theme}.png`);

    // fixed brass compass markers (MARKERS brass2 / brass8) and section rules
    L.markers.fixed.forEach((m) => {
      this.w(hmUI.widget.IMG, { x: px_(m.x), y: px_(m.y), src: `marker/${theme}/m${m.k}_brass.png`, show_level: NORMAL });
    });
    (L.rules || []).forEach((r) => {
      this.w(hmUI.widget.IMG, { x: px_(r.x), y: px_(r.y), src: `rule/${theme}_${r.src}.png`, show_level: NORMAL });
    });

    // gauges: every tick is its own short ARC_PROGRESS (no overlay mask), so the
    // result does not depend on how the firmware layers arcs and images.
    const g = L.gauge;
    this.settings.slots.forEach((id, i) => {
      const seg = g.segments[i];
      const unit = C.unit[id];
      const ticks = seg.ticks.map((t) => {
        const r = ARC_RADIUS_IS_CENTER ? t.r_center : t.r_outer;
        // whole-degree angles only: the firmware truncates arc angles (see geometry.tick_arc)
        const base = {
          center_x: px_(240), center_y: px_(240), radius: px_(r), line_width: px_(t.len),
          start_angle: t.s, end_angle: t.e, level: 100, corner_flag: 3, show_level: NORMAL,
        };
        const widget = this.w(hmUI.widget.ARC_PROGRESS, { ...base, color: unit.dim });
        return { widget, base, lit: false };
      });
      // the top- and bottom-middle gauges have a marker on the centre line (their 50% point)
      let marker = null;
      if (seg.marker) {
        const m = seg.marker;
        const base = m.base === 'brass' ? `m${m.k}_brass` : `m${m.k}_dim_${id}`;
        marker = {
          widget: this.w(hmUI.widget.IMG, { x: px_(m.x), y: px_(m.y), src: `marker/${theme}/${base}.png`, show_level: NORMAL }),
          k: m.k, base, after: m.after, lit: false,
        };
      }
      dyn.slots.push({ id, ticks, marker, progress: SENSOR_METRICS[id] && L.metrics[id].progress });
    });

    // complications
    this.settings.slots.forEach((id, i) => {
      const box = L.slots[i];
      const slot = dyn.slots[i];
      const bound = BOUND_METRICS[id];
      // CORNER_ROTATE mock: turned icon images, and glyph images laid along the gauge
      const rot = box.rot;
      const iconAt = rot && rot.icon ? { x: rot.icon.x, y: rot.icon.y, dir: `icons/${theme}/r${rot.set}` }
        : { x: box.icon.x, y: box.icon.y, dir: `icons/${theme}` };
      slot.iconDir = iconAt.dir;
      if (bound && bound.levelIcon) {
        // weather: the firmware picks the current condition's icon (no API level 1 property)
        slot.icon = this.w(hmUI.widget.IMG_LEVEL, {
          x: px_(iconAt.x), y: px_(iconAt.y),
          image_array: L.weather_desc.map((_, k) => `${iconAt.dir}/${bound.levelIcon}_${k}.png`),
          image_length: L.weather_desc.length, type: hmUI.data_type.WEATHER_CURRENT, show_level: NORMAL,
        });
      } else {
        slot.icon = this.w(hmUI.widget.IMG, {
          x: px_(iconAt.x), y: px_(iconAt.y), src: `${iconAt.dir}/${id}.png`, show_level: NORMAL,
        });
      }
      if (bound && hmUI.data_type[bound.type] !== undefined) {
        this.w(hmUI.widget.TEXT_FONT, {
          x: px_(box.value.x), y: px_(box.value.y), w: px_(box.value.w), h: px_(box.value.h),
          text_size: px_(box.value.size), color: C.text, font: L.font,
          align_h: hmUI.align.CENTER_H, align_v: hmUI.align.CENTER_V,
          type: hmUI.data_type[bound.type], unit_type: bound.unit, show_level: NORMAL,
        });
      } else if (rot) {
        slot.rot = rot;
        slot.glyphs = [0, 1, 2, 3, 4, 5, 6, 7].map(() => this.w(hmUI.widget.IMG, {
          x: 0, y: 0, w: px_(rot.q), h: px_(rot.q), src: 'rot/blank.png', show_level: NORMAL,
        }));
        if (!SENSOR_METRICS[id]) this.setRotValue(slot, { text: '--' });
      } else {
        slot.value = this.text(box.value, { color: C.text });
        slot.unit = this.text({ x: box.cx, y: box.unit.y, w: 40, h: box.unit.h, size: box.unit.size }, {
          color: C.unit[id] ? C.unit[id].on : C.muted, align_h: hmUI.align.LEFT,
        });
        if (!SENSOR_METRICS[id]) slot.value.setProperty(hmUI.prop.TEXT, '--');
      }
    });

    // glances: an "off" image is always shown (Bluetooth: connected icon; others: dim
    // outline); the system shows the active icon on top only while the status is on.
    const statusType = {
      disconnect: hmUI.system_status.DISCONNECT,
      dnd: hmUI.system_status.DISTURB,
      alarm: hmUI.system_status.CLOCK,
      lock: hmUI.system_status.LOCK,
    };
    L.glances.forEach((gl) => {
      if (statusType[gl.name] === undefined) return;
      this.w(hmUI.widget.IMG, {
        x: px_(gl.x), y: px_(gl.y), src: `status/${theme}/${gl.name}_off.png`, show_level: NORMAL,
      });
      this.w(hmUI.widget.IMG_STATUS, {
        x: px_(gl.x), y: px_(gl.y), type: statusType[gl.name], src: `status/${theme}/${gl.name}.png`, show_level: NORMAL,
      });
    });

    // date (left of the time), battery (right)
    dyn.dow = this.text(L.date.dow, { color: C.accent });
    dyn.day = this.text(L.date.day, { color: C.text });
    dyn.month = this.text(L.date.month, { color: C.muted });
    dyn.batteryIcon = this.w(hmUI.widget.IMG, {
      x: px_(L.battery.icon.x), y: px_(L.battery.icon.y), src: `battery/${theme}/high.png`, show_level: NORMAL,
    });
    dyn.battery = this.text(L.battery.text, { color: C.text });

    // time
    const timeStyle = theme === 'color' ? COLOR_TIME_STYLE : theme;
    // with no condition text (no weather slot) the time centres in the band by itself
    const hasDesc = this.settings.slots.indexOf('weather') >= 0;
    this.timeWidgets(`time/${timeStyle}`, hasDesc ? L.time : { ...L.time, y: L.time.y_alone }, NORMAL);
    // condition text: pre-rendered names picked by the firmware (current conditions).
    // Only shown when a slot shows weather: without the temperature it's out of context.
    if (this.settings.slots.indexOf('weather') >= 0) this.w(hmUI.widget.IMG_LEVEL, {
      x: px_(L.desc_img.x), y: px_(L.desc_img.y),
      image_array: L.weather_desc.map((_, i) => `desc/${theme}/${i}.png`), image_length: L.weather_desc.length,
      type: hmUI.data_type.WEATHER_CURRENT, show_level: NORMAL,
    });

    // ------------------------------------------------------------ always-on
    this.w(hmUI.widget.IMG, { x: 0, y: 0, src: C.aod_bg, show_level: AOD });
    this.timeWidgets(`aod/time_${theme}`, { ...L.time, y: L.time.y_aod }, AOD);
    const aodText = (box, color) => this.text(box, { color, show_level: AOD });
    dyn.aodDow = aodText(L.aod.date.dow, C.aod_text);
    dyn.aodDay = aodText(L.aod.date.day, C.aod_text);
    dyn.aodMonth = aodText(L.aod.date.month, C.aod_text);
    this.w(hmUI.widget.IMG, {
      x: px_(L.aod.battery.icon.x), y: px_(L.aod.battery.icon.y), src: `aod/battery_${theme}.png`, show_level: AOD,
    });
    dyn.aodBattery = aodText(L.aod.battery.text, C.aod_text);
  },

  timeWidgets(dir, T, level) {
    const digits = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((d) => `${dir}/${d}.png`);
    this.w(hmUI.widget.IMG_TIME, {
      hour_zero: 1, hour_startX: px_(T.hour_x), hour_startY: px_(T.y), hour_array: digits,
      hour_space: 0, hour_align: hmUI.align.LEFT, show_level: level,
    });
    this.w(hmUI.widget.IMG, { x: px_(T.colon_x), y: px_(T.y), src: `${dir}/colon.png`, show_level: level });
    this.w(hmUI.widget.IMG_TIME, {
      minute_zero: 1, minute_startX: px_(T.minute_x), minute_startY: px_(T.y), minute_array: digits,
      minute_space: 0, minute_align: hmUI.align.LEFT, show_level: level,
    });
  },

  // ---------------------------------------------------------------- updates
  update() {
    const dyn = this.dyn;
    if (!dyn) return;
    const time = this.timeSensor;
    const theme = this.theme;
    const C = L.colors[theme];

    // date
    const dow = WEEKDAYS[((time.week || 1) - 1 + 7) % 7];
    const month = MONTHS[((time.month || 1) - 1 + 12) % 12];
    const day = String(time.day || 1);
    [[dyn.dow, dyn.aodDow, dow], [dyn.day, dyn.aodDay, day], [dyn.month, dyn.aodMonth, month]].forEach(([a, b, v]) => {
      a.setProperty(hmUI.prop.TEXT, v);
      b.setProperty(hmUI.prop.TEXT, v);
    });

    // battery
    const level = this.batterySensor ? this.batterySensor.current || 0 : 0;
    const band = level > 40 ? 'high' : level > 20 ? 'mid' : 'low';
    dyn.batteryIcon.setProperty(hmUI.prop.SRC, `battery/${theme}/${band}.png`);
    dyn.battery.setProperty(hmUI.prop.TEXT, `${level}%`);
    dyn.aodBattery.setProperty(hmUI.prop.TEXT, `${level}%`);

    // complications
    const ctx = {
      time,
      is12h: hmSetting.getTimeFormat() === 0,
      imperial: typeof hmSetting.getMileageUnit === 'function' && hmSetting.getMileageUnit() === 1,
    };
    dyn.slots.forEach((slot, i) => {
      const def = SENSOR_METRICS[slot.id];
      if (!def) return;
      const sensor = this.sensor(def.sensor);
      const r = sensor ? def.read(sensor, ctx) : { text: '--', progress: null };
      this.setValue(i, slot, r, C);
      if (r.icon) slot.icon.setProperty(hmUI.prop.SRC, `${slot.iconDir}/${r.icon}.png`);
      if (slot.progress) this.setTicks(slot, r.progress);
    });
  },

  /** CORNER_ROTATE: lay the value (and unit) glyph images along the gauge's direction. */
  setRotValue(slot, r) {
    const R = slot.rot;
    const cw = L.char_widths;
    const items = [];
    for (let k = 0; k < r.text.length; k++) items.push({ c: r.text[k], w: cw.value[r.text[k]] || cw.value['0'], u: false });
    if (r.unit) {
      items.push({ c: null, w: cw.unit_gap });
      for (let k = 0; k < r.unit.length; k++) items.push({ c: r.unit[k], w: cw.unit[r.unit[k]] || 0, u: true });
    }
    const total = items.reduce((a, it) => a + it.w, 0);
    let s = -total / 2;
    let n = 0;
    const dir = `rot/${this.theme}/${R.set}_`;
    items.forEach((it) => {
      const mid = s + it.w / 2;
      s += it.w;
      const code = it.u ? `u_${slot.id}_${it.c}` : ROT_CODES[it.c];
      if (!it.c || !code || n >= slot.glyphs.length) return;
      slot.glyphs[n++].setProperty(hmUI.prop.MORE, {
        x: px_(Math.round(R.vx + R.cos * mid - R.q / 2)), y: px_(Math.round(R.vy + R.sin * mid - R.q / 2)),
        w: px_(R.q), h: px_(R.q), src: `${dir}${code}.png`,
      });
    });
    for (; n < slot.glyphs.length; n++) slot.glyphs[n].setProperty(hmUI.prop.SRC, 'rot/blank.png');
  },

  setValue(i, slot, r, C) {
    if (slot.rot) {
      this.setRotValue(slot, r);
      return;
    }
    const box = L.slots[i];
    slot.value.setProperty(hmUI.prop.TEXT, r.text);
    if (!r.unit) {
      slot.unit.setProperty(hmUI.prop.TEXT, '');
      return;
    }
    // centre "value + unit" as one block using the generated advance widths
    const cw = L.char_widths;
    const wv = textWidth(r.text, cw.value);
    const wu = textWidth(r.unit, cw.unit);
    const left = box.cx - (wv + cw.unit_gap + wu) / 2;
    slot.value.setProperty(hmUI.prop.MORE, {
      x: px_(left), y: px_(box.value.y), w: px_(wv + 4), h: px_(box.value.h),
      text: r.text, text_size: px_(box.value.size), color: C.text, font: L.font,
      align_h: hmUI.align.LEFT, align_v: hmUI.align.CENTER_V,
    });
    slot.unit.setProperty(hmUI.prop.MORE, {
      x: px_(left + wv + cw.unit_gap), y: px_(box.unit.y), w: px_(wu + 6), h: px_(box.unit.h),
      text: r.unit, text_size: px_(box.unit.size), color: C.unit[slot.id].on, font: L.font,
      align_h: hmUI.align.LEFT, align_v: hmUI.align.CENTER_V,
    });
  },

  /** Light the first round(progress * N) ticks in fill order; only changed ticks are touched. */
  setTicks(slot, progress) {
    const n = progress == null ? 0 : Math.max(0, Math.min(slot.ticks.length, Math.round(progress * slot.ticks.length)));
    const unit = L.colors[this.theme].unit[slot.id];
    slot.ticks.forEach((t, k) => {
      const lit = k < n;
      if (lit === t.lit) return;
      t.lit = lit;
      t.widget.setProperty(hmUI.prop.MORE, { ...t.base, color: lit ? unit.on : unit.dim });
    });
    const m = slot.marker;
    if (m) {
      const lit = n > m.after;
      if (lit !== m.lit) {
        m.lit = lit;
        m.widget.setProperty(hmUI.prop.SRC, `marker/${this.theme}/${lit ? `m${m.k}_lit_${slot.id}` : m.base}.png`);
      }
    }
  },
});
