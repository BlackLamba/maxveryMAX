/**
 * Билет-карточка события (DESIGN.md §3.1): корешок с датой + перфорация +
 * тело. Не «SaaS-карточка»: плоская, без теней, двухзонная, с вырезами.
 *
 * Контракт данных:
 * - price_display показываем as-is (не пересобираем из min/max);
 * - data_origin === 'mock' → плашка «демо» (обязательная маркировка);
 * - reason — короткая подпись, как пришла из API;
 * - age_limit — бейдж;
 * - корешок залит Lamp, если событие сегодня и ещё не началось, либо идёт
 *   сейчас («фонарь горит»).
 */
import type { MouseEvent } from 'react';
import { Link } from 'react-router-dom';
import type { EventOut } from '@/types/api';
import { useFavorites } from '@/hooks/useFavorites';
import {
  dayNumber,
  formatKm,
  formatTime,
  isHappeningNow,
  isStarted,
  isToday,
  monthShort,
  parseApiDate,
} from '@/utils/format';
import { Icon } from '@/components/Icon';
import { T } from '@/utils/texts';

interface Props {
  ev: EventOut;
  /** показывать город отдельной строкой (лента «Все города», закладки) */
  showCity?: boolean;
}

export function TicketCard({ ev, showCity = false }: Props) {
  const fav = useFavorites();
  const saved = fav.has(ev.id);
  const now = isHappeningNow(ev.starts_at, ev.ends_at);
  const upcomingToday = isToday(ev.starts_at) && !isStarted(ev.starts_at);
  const hot = now || upcomingToday;
  const ended =
    (ev.ends_at ? parseApiDate(ev.ends_at).getTime() : parseApiDate(ev.starts_at).getTime() + 3 * 3_600_000) <
    Date.now();

  const onToggleFav = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    void fav.toggle(ev);
  };

  return (
    <Link
      to={`/event/${ev.id}`}
      className={[
        'ticket',
        hot ? 'ticket--hot' : '',
        ended ? 'ticket--ended' : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <div className="ticket__stub" aria-hidden="true">
        <span className="ticket__day t-date-hero">{dayNumber(ev.starts_at)}</span>
        <span className="ticket__month caption">{monthShort(ev.starts_at)}</span>
        <span className="ticket__time caption tnum">{formatTime(ev.starts_at)}</span>
        {now && <span className="ticket__live">{T.card.now}</span>}
      </div>

      <div className="ticket__body">
        {ev.image_url && (
          <img className="ticket__photo" src={ev.image_url} alt="" loading="lazy" />
        )}
        <h3 className="ticket__title t-card-title">{ev.title}</h3>
        <p className="ticket__venue body">{ev.venue_name ?? T.card.venueUnknown}</p>
        {showCity && <p className="ticket__city caption muted">{ev.city_name}</p>}

        <div className="ticket__plates">
          <span className={`plate${ev.is_free ? ' plate--free' : ''}`}>{ev.price_display}</span>
          {ev.age_limit && <span className="plate plate--age">{ev.age_limit}</span>}
          {ev.distance_km != null && (
            <span className="plate tnum">{formatKm(ev.distance_km)}</span>
          )}
          {ended && <span className="plate plate--muted">завершилось</span>}
          {ev.data_origin === 'mock' && (
            <span className="plate plate--demo" title="Демо-данные: событие из тестового набора">
              демо
            </span>
          )}
        </div>

        {ev.reason && <p className="ticket__reason caption">{ev.reason}</p>}
      </div>

      <button
        type="button"
        className={`ticket__fav${saved ? ' ticket__fav--on' : ''}`}
        onClick={onToggleFav}
        aria-pressed={saved}
        aria-label={saved ? `${T.card.removeFavorite}: ${ev.title}` : `${T.card.addFavorite}: ${ev.title}`}
      >
        <Icon name={saved ? 'bookmark-filled' : 'bookmark'} size={20} />
      </button>
    </Link>
  );
}
