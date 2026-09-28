/**
 * Дата-линейка (DESIGN.md §3.1): 7 дней вперёд крупными числами (Oswald) —
 * первая ось выбора «когда?». Сегодняшний день помечен янтарным «сегодня»,
 * выбранный день — янтарная плашка. «Все даты» сбрасывает диапазон.
 *
 * Одиночный тап = один день (date_from = date_to) — так же работает
 * временное окно в фильтрах (контракт EventFilters).
 */
import { useMemo } from 'react';
import {
  addDaysKey,
  dayNumberKey,
  monthShortKey,
  todayKey,
  weekdayShortKey,
} from '@/utils/format';
import { T } from '@/utils/texts';

interface Props {
  dateFrom: string | null;
  dateTo: string | null;
  onSelect: (key: string | null) => void;
}

const DAYS_AHEAD = 7;

export function DateRuler({ dateFrom, dateTo, onSelect }: Props) {
  const days = useMemo(() => {
    const today = todayKey();
    return Array.from({ length: DAYS_AHEAD }, (_, i) => addDaysKey(today, i));
  }, []);
  const today = days[0];
  const single = dateFrom !== null && dateFrom === dateTo ? dateFrom : null;
  const rangeActive = dateFrom !== null && dateFrom !== dateTo;

  return (
    <div className="ruler" role="group" aria-label="Дата события">
      <button
        type="button"
        className={`ruler__all ui${dateFrom === null ? ' ruler__all--on' : ''}`}
        onClick={() => onSelect(null)}
        aria-pressed={dateFrom === null}
      >
        {T.feed.allDates}
      </button>

      <div className="ruler__track">
        {days.map((key) => {
          const selected = single === key;
          const isToday = key === today;
          const inRange =
            rangeActive && dateFrom !== null && dateTo !== null && key >= dateFrom && key <= dateTo;
          return (
            <button
              key={key}
              type="button"
              className={[
                'ruler__day',
                selected ? 'ruler__day--selected' : '',
                inRange ? 'ruler__day--in-range' : '',
              ]
                .filter(Boolean)
                .join(' ')}
              onClick={() => onSelect(selected ? null : key)}
              aria-pressed={selected}
              aria-label={`${dayNumberKey(key)} ${monthShortKey(key)}, ${weekdayShortKey(key)}${
                isToday ? ` (${T.feed.todayMark})` : ''
              }`}
            >
              <span className={`ruler__wd caption${isToday ? ' ruler__wd--today' : ''}`}>
                {isToday ? T.feed.todayMark : weekdayShortKey(key)}
              </span>
              <span className="ruler__num t-date-hero">{dayNumberKey(key)}</span>
              <span className="ruler__mon caption">{monthShortKey(key)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
