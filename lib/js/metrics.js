/**
 * Complication definitions.
 *
 * Two kinds of metric:
 *  - "sensor" metrics read an hmSensor directly, so the face controls formatting
 *    (thousands separators, units, "--" placeholders) and gauge progress.
 *  - "bound" metrics use the system's data binding (TEXT_FONT / ARC_PROGRESS `type`),
 *    for data that has no API level 1 sensor (floors, SpO2, stress, UV, ...).
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
      const current = s.current || 0;
      const target = s.target || 8000;
      return { text: formatThousands(current), progress: current / target };
    },
  },
  heart: {
    sensor: 'HEART',
    event: 'LAST',
    read(s) {
      const last = s.last || 0;
      return { text: last > 0 ? String(last) : '--', progress: null };
    },
  },
  distance: {
    sensor: 'DISTANCE',
    read(s, ctx) {
      const { text, unit } = formatDistance(s.current || 0, ctx.imperial);
      return { text, unit, progress: null };
    },
  },
  calories: {
    sensor: 'CALORIE',
    read(s) {
      const current = s.current || 0;
      const target = s.target || 300;
      return { text: formatThousands(current), progress: current / target };
    },
  },
  pai: {
    sensor: 'PAI',
    read(s) {
      const total = s.totalpai || 0;
      return { text: String(total), progress: total / 100 };
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

/** Metrics drawn by the system. `type` is the hmUI.data_type key. */
export const BOUND_METRICS = {
  floors: { type: 'FLOOR', unit: 0, progress: true },
  stand: { type: 'STAND', unit: 0, progress: true },
  fatburn: { type: 'FAT_BURNING', unit: 0, progress: true },
  spo2: { type: 'SPO2', unit: 1, progress: false },
  stress: { type: 'STRESS', unit: 0, progress: false },
  uvi: { type: 'UVI', unit: 0, progress: false },
  humidity: { type: 'HUMIDITY', unit: 1, progress: false },
  // current temperature; the icon is an IMG_LEVEL of condition icons bound to the same data
  weather: { type: 'WEATHER_CURRENT', unit: 1, progress: false, levelIcon: 'weather' },
  aqi: { type: 'AQI', unit: 0, progress: false },
};
