/**
 * Complication definitions.
 *
 * Two kinds of metric:
 *  - "sensor" metrics read an @zos/sensor directly, so the face controls formatting
 *    (thousands separators, units, "--" placeholders) and gauge progress.
 *  - "bound" metrics use the system's data binding (TEXT_FONT / IMG_LEVEL `type`),
 *    for data no sensor exposes at API level 4.2 (floors, current weather, UV,
 *    humidity, air quality).
 */
import { formatThousands, formatDistance, formatClock } from './format';
import { nextSunEvent } from './sun';

/** Order here = order in the on-watch editor list. */
export const METRIC_IDS = [
  'steps', 'heart', 'distance', 'calories', 'floors', 'pai', 'stand',
  'fatburn', 'spo2', 'stress', 'uvi', 'humidity', 'aqi', 'sun', 'weather',
];

export const SENSOR_METRICS = {
  steps: {
    sensor: 'STEP',
    read(s) {
      const current = s.getCurrent() || 0;
      const target = s.getTarget() || 8000;
      return { text: formatThousands(current), progress: current / target };
    },
  },
  heart: {
    sensor: 'HEART',
    event: 'LAST',
    read(s) {
      const last = s.getLast() || 0;
      return { text: last > 0 ? String(last) : '--', progress: null };
    },
  },
  distance: {
    sensor: 'DISTANCE',
    read(s, ctx) {
      const { text, unit } = formatDistance(s.getCurrent() || 0, ctx.imperial);
      return { text, unit, progress: null };
    },
  },
  calories: {
    sensor: 'CALORIE',
    read(s) {
      const current = s.getCurrent() || 0;
      const target = s.getTarget() || 300;
      return { text: formatThousands(current), progress: current / target };
    },
  },
  pai: {
    sensor: 'PAI',
    read(s) {
      const total = s.getTotal() || 0;
      return { text: String(total), progress: total / 100 };
    },
  },
  stand: {
    sensor: 'STAND',
    read(s) {
      const current = s.getCurrent() || 0;
      const target = s.getTarget() || 12;
      return { text: String(current), progress: current / target };
    },
  },
  fatburn: {
    sensor: 'FAT_BURNING',
    read(s) {
      const current = s.getCurrent() || 0;
      const target = s.getTarget() || 30;
      return { text: String(current), progress: current / target };
    },
  },
  spo2: {
    sensor: 'SPO2',
    read(s) {
      const r = s.getCurrent();
      const v = r && r.value;
      return { text: v > 0 ? `${v}%` : '--', progress: null };
    },
  },
  stress: {
    sensor: 'STRESS',
    read(s) {
      const r = s.getCurrent();
      const v = r && r.value;
      return { text: v > 0 ? String(v) : '--', progress: null };
    },
  },
  sun: {
    sensor: 'WEATHER',
    read(s, ctx) {
      const ev = nextSunEvent(s, ctx.time);
      if (!ev) return { text: '--:--', progress: null, icon: 'sun' };
      return {
        text: formatClock(ev.hour, ev.minute, ctx.is12h),
        progress: null,
        icon: ev.type === 'sunrise' ? 'sunrise' : 'sun',
      };
    },
  },
};

/** Metrics drawn by the system (no sensor exposes them). `type` is the data_type key. */
export const BOUND_METRICS = {
  floors: { type: 'FLOOR', unit: 0, progress: true },
  uvi: { type: 'UVI', unit: 0, progress: false },
  humidity: { type: 'HUMIDITY', unit: 1, progress: false },
  // current temperature; the icon is an IMG_LEVEL of condition icons bound to the same data
  weather: { type: 'WEATHER_CURRENT', unit: 1, progress: false, levelIcon: 'weather' },
  aqi: { type: 'AQI', unit: 0, progress: false },
};
