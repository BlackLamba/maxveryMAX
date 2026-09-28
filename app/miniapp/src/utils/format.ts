/**
 * Форматирование дат/времени/расстояний.
 *
 * КОНТРАКТ ВРЕМЕНИ (сверено с backend):
 * - starts_at/ends_at приходят строками NAIVE UTC: «2026-09-26T16:00:00»
 *   (= 19:00 МСК). Парсим как UTC, показываем в часовом поясе города.
 * - Оффсет города API не отдаёт (CityOut без tz); все демо-города UTC+3,
 *   default_tz_offset_hours=3 в backend/app/config.py → CITY_TZ_OFFSET = 3.
 * - date_from/date_to/time_from/time_to ОТПРАВЛЯЕМ как локальные (городские)
 *   дату/время — бэкенд сам переводит их в UTC-границы (services/timeutils.py).
 * - Временное окно time_from/time_to валидно только при date_from === date_to.
 */

export const CITY_TZ_OFFSET = 3;

const MONTHS_SHORT = [
  'янв', 'фев', 'мар', 'апр', 'май', 'июн',
  'июл', 'авг', 'сен', 'окт', 'ноя', 'дек',
];
const MONTHS_GENITIVE = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
];
const WEEKDAYS_SHORT = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
const WEEKDAYS_LONG = [
  'воскресенье', 'понедельник', 'вторник', 'среда',
  'четверг', 'пятница', 'суббота',
];

/** Naive-UTC строка API → Date (момент времени). */
export function parseApiDate(s: string): Date {
  return new Date(s.endsWith('Z') || s.includes('+') ? s : `${s}Z`);
}

/**
 * Сдвинутая «псевдолокальная» дата: её UTC-геттеры возвращают значения
 * в часовом поясе города (UTC+3). Все функции ниже работают через неё.
 */
function cityDate(d: Date): Date {
  return new Date(d.getTime() + CITY_TZ_OFFSET * 3_600_000);
}

/** Текущее «городское» время. */
export function cityNow(): Date {
  return cityDate(new Date());
}

/** YYYY-MM-DD (локальная дата города) — формат date_from/date_to для API. */
export function dateKey(d: Date): string {
  const c = cityDate(d);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${c.getUTCFullYear()}-${p(c.getUTCMonth() + 1)}-${p(c.getUTCDate())}`;
}

export function todayKey(): string {
  return dateKey(new Date());
}

export function addDaysKey(baseKey: string, days: number): string {
  const [y, m, d] = baseKey.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + days));
  const p = (n: number) => String(n).padStart(2, '0');
  return `${dt.getUTCFullYear()}-${p(dt.getUTCMonth() + 1)}-${p(dt.getUTCDate())}`;
}

/** Ключ даты события (для сопоставления с дата-линейкой). */
export function eventDayKey(iso: string): string {
  return dateKey(parseApiDate(iso));
}

/** «19:00» */
export function formatTime(iso: string): string {
  const c = cityDate(parseApiDate(iso));
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(c.getUTCHours())}:${p(c.getUTCMinutes())}`;
}

/** «26» — число дня (корешок билета, дата-линейка). */
export function dayNumber(iso: string): string {
  return String(cityDate(parseApiDate(iso)).getUTCDate());
}

/** «сен» */
export function monthShort(iso: string): string {
  return MONTHS_SHORT[cityDate(parseApiDate(iso)).getUTCMonth()];
}

/** «сб» */
export function weekdayShort(iso: string): string {
  return WEEKDAYS_SHORT[cityDate(parseApiDate(iso)).getUTCDay()];
}

/** «сегодня» / «завтра» / «26 сентября» */
export function dayLabelIso(iso: string): string {
  return dayLabelKey(eventDayKey(iso));
}

export function dayLabelKey(key: string): string {
  const today = todayKey();
  if (key === today) return 'сегодня';
  if (key === addDaysKey(today, 1)) return 'завтра';
  const [y, m, d] = key.split('-').map(Number);
  return `${d} ${MONTHS_GENITIVE[m - 1]}${y === new Date().getUTCFullYear() ? '' : ` ${y}`}`;
}

/** «суббота, 26 сентября» — крупная дата в карточке события. */
export function fullDateLabel(iso: string): string {
  const c = cityDate(parseApiDate(iso));
  return `${WEEKDAYS_LONG[c.getUTCDay()]}, ${c.getUTCDate()} ${MONTHS_GENITIVE[c.getUTCMonth()]}`;
}

/** «19:00 — 21:30»; если конец в следующие сутки — «19:00 — 21:30 (+1 день)». */
export function formatTimeRange(startIso: string, endIso: string | null): string {
  const from = formatTime(startIso);
  if (!endIso) return `начало в ${from}`;
  const to = formatTime(endIso);
  const crossDay = eventDayKey(endIso) !== eventDayKey(startIso);
  return crossDay ? `${from} — ${to} (+1 день)` : `${from} — ${to}`;
}

/** «идёт сейчас» — событие началось и ещё не закончилось. */
export function isHappeningNow(startIso: string, endIso: string | null): boolean {
  const now = Date.now();
  const start = parseApiDate(startIso).getTime();
  const end = endIso ? parseApiDate(endIso).getTime() : start + 3 * 3_600_000;
  return start <= now && now <= end;
}

export function isToday(startIso: string): boolean {
  return eventDayKey(startIso) === todayKey();
}

/** Началось ли событие (для приглушения карточек, которые уже идут/прошли). */
export function isStarted(startIso: string): boolean {
  return parseApiDate(startIso).getTime() <= Date.now();
}

/** «1.2 км» / «800 м» */
export function formatKm(km: number): string {
  return km < 1 ? `${Math.round(km * 1000)} м` : `${km.toFixed(1).replace('.', ',')} км`;
}

/** «1 500 ₽» — для подписи слайдера бюджета (цена приходит готовой строкой,
 *  а вот слайдер формируем сами). */
export function formatRub(n: number): string {
  return `${n.toLocaleString('ru-RU')} ₽`;
}

/** «5 событий», «21 событие», «2 события» */
export function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return `${n} ${one}`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} ${few}`;
  return `${n} ${many}`;
}

export function eventsWord(n: number): string {
  return plural(n, 'событие', 'события', 'событий');
}

/** «25 сен — 30 сен» для чипа активного диапазона. */
export function shortRangeLabel(fromKey: string, toKey: string): string {
  const label = (k: string) => {
    const [y, m, d] = k.split('-').map(Number);
    void y;
    return `${d} ${MONTHS_SHORT[m - 1]}`;
  };
  return fromKey === toKey ? label(fromKey) : `${label(fromKey)} — ${label(toKey)}`;
}

/* --- Хелперы для ключей дат YYYY-MM-DD (дата-линейка) --- */

function keyParts(key: string): Date {
  const [y, m, d] = key.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

export function dayNumberKey(key: string): string {
  return String(keyParts(key).getUTCDate());
}

export function monthShortKey(key: string): string {
  return MONTHS_SHORT[keyParts(key).getUTCMonth()];
}

export function weekdayShortKey(key: string): string {
  return WEEKDAYS_SHORT[keyParts(key).getUTCDay()];
}

/** «25 сентября» из ключа — для заголовка выбранного дня. */
export function dayLabelLongKey(key: string): string {
  const c = keyParts(key);
  return `${c.getUTCDate()} ${MONTHS_GENITIVE[c.getUTCMonth()]}`;
}
