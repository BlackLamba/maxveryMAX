/**
 * Разбор параметров запуска (deep link от бота).
 *
 * Источники (по приоритету):
 * 1. window.WebApp.initDataUnsafe.start_param — payload deep link'а MAX
 *    (https://max.ru/<bot>?startapp=<payload>, ≤ 512 символов).
 *    Компактный формат: «city=moscow&cat=concert,theater&date=2026-09-25&budget=1500».
 *    Разделители «&» и «;» (в deep link'ах «&» может теряться), значения могут
 *    быть URL-закодированы.
 * 2. Браузерный фолбэк для отладки: ?query ДО hash и query внутри hash
 *    (HashRouter): #/?city=moscow. Принимаются и компактные, и полные имена
 *    параметров (city_id, date_from, …) — как в EventFilters.
 *
 * Всё найденное применяется к фильтрам ПЕРЕД первым запросом /api/events.
 */
import { CATEGORY_SLUGS, type CategorySlug } from '@shared/categories';
import { getStartParam } from '@/utils/platform';
import type { SortOption } from '@/types/api';

export interface LaunchFilters {
  /** slug («moscow») или числовой id города */
  city?: string;
  categories?: CategorySlug[];
  dateFrom?: string; // YYYY-MM-DD
  dateTo?: string;
  timeFrom?: string; // HH:MM
  timeTo?: string;
  priceMax?: number;
  isFree?: boolean;
  lat?: number;
  lon?: number;
  radiusKm?: number;
  sort?: SortOption;
  /** сразу открыть карточку события (deep link на конкретное событие) */
  eventId?: number;
}

const SORTS: SortOption[] = ['relevance', 'date_asc', 'price_asc', 'price_desc', 'distance'];
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TIME_RE = /^\d{2}:\d{2}(:\d{2})?$/;

function parsePairs(raw: string): Array<[string, string]> {
  let s = raw.trim();
  // start_param мог прийти URL-закодированным («city%3Dmoscow%26cat%3D...»)
  if (!s.includes('=') && s.includes('%')) {
    try {
      s = decodeURIComponent(s);
    } catch {
      /* оставляем как есть */
    }
  }
  const pairs: Array<[string, string]> = [];
  for (const chunk of s.split(/[&;]/)) {
    const i = chunk.indexOf('=');
    if (i <= 0) continue;
    let key = chunk.slice(0, i).trim().toLowerCase();
    let val = chunk.slice(i + 1).trim();
    try {
      val = decodeURIComponent(val.replace(/\+/g, ' '));
    } catch {
      /* оставляем как есть */
    }
    // полные имена из EventFilters → компактные
    key = key.replace(/^city_id$/, 'city').replace(/^category$/, 'cat')
      .replace(/^price_max$/, 'budget').replace(/^is_free$/, 'free')
      .replace(/^radius_km$/, 'radius').replace(/^event_id$/, 'event');
    if (key && val) pairs.push([key, val]);
  }
  return pairs;
}

function browserParams(): Array<[string, string]> {
  const pairs: Array<[string, string]> = [];
  const push = (sp: URLSearchParams) => {
    sp.forEach((v, k) => pairs.push([k.toLowerCase(), v]));
  };
  if (typeof window === 'undefined') return pairs;
  push(new URLSearchParams(window.location.search));
  const hash = window.location.hash;
  const q = hash.indexOf('?');
  if (q >= 0) push(new URLSearchParams(hash.slice(q + 1)));
  return pairs;
}

function toCategories(raw: string): CategorySlug[] | undefined {
  const out = raw
    .split(/[;,]/)
    .map((s) => s.trim().toLowerCase())
    .filter((s): s is CategorySlug => (CATEGORY_SLUGS as readonly string[]).includes(s));
  return out.length > 0 ? out : undefined;
}

function toNumber(raw: string): number | undefined {
  const s = raw.trim();
  if (!s) return undefined; // Number('') === 0 — не ловимся: пустое ≠ ноль
  const n = Number(s.replace(',', '.'));
  return Number.isFinite(n) ? n : undefined;
}

/** Собирает LaunchFilters из start_param и браузерного query. */
export function readLaunchParams(): LaunchFilters {
  const merged = new Map<string, string>();
  // deep link от бота — приоритет
  const sp = getStartParam();
  if (sp) for (const [k, v] of parsePairs(sp)) merged.set(k, v);
  // браузерный фолбэк: только если deep link не дал значения
  for (const [k, v] of browserParams()) if (!merged.has(k)) merged.set(k, v);

  const out: LaunchFilters = {};
  const city = merged.get('city');
  if (city) out.city = city;

  const cat = merged.get('cat');
  if (cat) out.categories = toCategories(cat);

  const date = merged.get('date');
  const dateFrom = merged.get('date_from') ?? (date && DATE_RE.test(date) ? date : undefined);
  const dateTo = merged.get('date_to') ?? dateFrom;
  if (dateFrom && DATE_RE.test(dateFrom)) out.dateFrom = dateFrom;
  if (dateTo && DATE_RE.test(dateTo)) out.dateTo = dateTo;

  const tf = merged.get('time_from');
  const tt = merged.get('time_to');
  // временное окно бэкенд принимает только вместе с одним днём (date_from === date_to)
  if (tf && TIME_RE.test(tf) && out.dateFrom && out.dateFrom === out.dateTo) {
    out.timeFrom = tf.slice(0, 5);
  }
  if (tt && TIME_RE.test(tt) && out.dateFrom && out.dateFrom === out.dateTo) {
    out.timeTo = tt.slice(0, 5);
  }

  const budget = merged.get('budget');
  if (budget !== undefined) {
    const n = toNumber(budget);
    if (n !== undefined && n >= 0) out.priceMax = Math.round(n);
  }

  const free = merged.get('free');
  if (free === '1' || free === 'true' || free === 'yes') out.isFree = true;

  const lat = toNumber(merged.get('lat') ?? '');
  const lon = toNumber(merged.get('lon') ?? '');
  if (lat !== undefined && lon !== undefined && Math.abs(lat) <= 90 && Math.abs(lon) <= 180) {
    out.lat = lat;
    out.lon = lon;
    const radius = toNumber(merged.get('radius') ?? '');
    if (radius !== undefined && radius > 0 && radius <= 200) out.radiusKm = radius;
  }

  const sort = merged.get('sort');
  if (sort && (SORTS as string[]).includes(sort)) out.sort = sort as SortOption;

  const event = toNumber(merged.get('event') ?? '');
  if (event !== undefined && Number.isInteger(event) && event > 0) out.eventId = event;

  return out;
}
