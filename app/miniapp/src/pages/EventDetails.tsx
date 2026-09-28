/**
 * Экран 2 — Карточка события (задача п.5.2).
 * GET /api/events/{id} (фильтры ленты передаём в query — они влияют на
 * reason «почему подходит»). «Купить билет»: сначала POST /events/{id}/click
 * (метрика пилота), затем переход по source_url — WebApp.openLink внутри MAX
 * или window.open в браузере. Закладка — toggle из FavoritesProvider.
 * Кнопка «Назад» хоста MAX (BackButton) синхронизирована с роутером.
 */
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ApiError, api } from '@/api/client';
import type { EventOut } from '@/types/api';
import { useFiltersState } from '@/hooks/useFilters';
import { useFavorites } from '@/hooks/useFavorites';
import { useMaxUI } from '@/components/MaxUIProvider';
import { DetailSkeleton, ErrorState, NotFoundState } from '@/components/StateViews';
import { Icon } from '@/components/Icon';
import {
  dayNumber,
  formatKm,
  formatTimeRange,
  fullDateLabel,
  isHappeningNow,
  monthShort,
} from '@/utils/format';
import { haptic, openExternal, withHostBackButton } from '@/utils/platform';
import { T } from '@/utils/texts';

type Status = 'loading' | 'ready' | 'error' | 'not-found';

export function EventDetails() {
  const { id } = useParams<{ id: string }>();
  const eventId = Number(id);
  const navigate = useNavigate();
  const F = useFiltersState();
  const fav = useFavorites();
  const { userId } = useMaxUI();

  const [event, setEvent] = useState<EventOut | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [error, setError] = useState<ApiError | null>(null);
  const [nonce, setNonce] = useState(0);
  const [opening, setOpening] = useState(false);

  const goBack = useCallback(() => {
    if (window.history.state && window.history.state.idx > 0) navigate(-1);
    else navigate('/', { replace: true });
  }, [navigate]);

  // Кнопка «Назад» в шапке MAX (в браузере — no-op, есть своя «‹»).
  useEffect(() => withHostBackButton(goBack), [goBack]);

  // Контекст фильтров — только для reason (контракт GET /events/{id})
  const ctxQuery = useMemo(() => {
    const q = F.toQuery();
    delete q.limit;
    delete q.offset;
    delete q.sort;
    return q;
  }, [F.toQuery]);
  const ctxKey = JSON.stringify(ctxQuery);

  useEffect(() => {
    if (!Number.isInteger(eventId) || eventId <= 0) {
      setStatus('not-found');
      return;
    }
    const ac = new AbortController();
    setStatus('loading');
    api
      .event(eventId, ctxQuery, ac.signal)
      .then((ev) => {
        setEvent(ev);
        setStatus('ready');
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') return;
        if (err instanceof ApiError && err.status === 404) {
          setStatus('not-found');
          return;
        }
        setError(
          err instanceof ApiError
            ? err
            : new ApiError(0, 'network_error', 'нет соединения', undefined, true),
        );
        setStatus('error');
      });
    return () => ac.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId, ctxKey, nonce]);

  const onBuy = useCallback(async () => {
    if (!event?.source_url || opening) return;
    setOpening(true);
    haptic('medium');
    try {
      // лог перехода — ДО открытия источника (задача п.4)
      await api.logClick(event.id, userId, {
        screen: 'details',
        platform: navigator.userAgent.slice(0, 120),
      });
    } catch {
      // аналитика не должна блокировать пользователя
    }
    openExternal(event.source_url);
    // даём Bridge/браузеру обработать клик, снимаем состояние
    window.setTimeout(() => setOpening(false), 600);
  }, [event, opening, userId]);

  if (status === 'loading') {
    return (
      <div className="page page--detail">
        <DetailHeader onBack={goBack} />
        <DetailSkeleton />
      </div>
    );
  }

  if (status === 'not-found') {
    return (
      <div className="page page--detail">
        <DetailHeader onBack={goBack} />
        <NotFoundState
          action={
            <Link to="/" className="btn btn--ghost state__action">
              {T.details.backToFeed}
            </Link>
          }
        />
      </div>
    );
  }

  if (status === 'error' || !event) {
    return (
      <div className="page page--detail">
        <DetailHeader onBack={goBack} />
        <ErrorState error={error} onRetry={() => setNonce((n) => n + 1)} />
      </div>
    );
  }

  const saved = fav.has(event.id);
  const now = isHappeningNow(event.starts_at, event.ends_at);

  return (
    <div className="page page--detail">
      <DetailHeader
        onBack={goBack}
        right={
          <button
            type="button"
            className={`icon-btn${saved ? ' icon-btn--on' : ''}`}
            onClick={() => void fav.toggle(event)}
            aria-pressed={saved}
            aria-label={saved ? T.card.removeFavorite : T.card.addFavorite}
          >
            <Icon name={saved ? 'bookmark-filled' : 'bookmark'} size={21} />
          </button>
        }
      />

      <main className="detail">
        <div className="detail__topline">
          <span className="detail__category caption">{event.category_name}</span>
          {now && <span className="live-pill caption">{T.card.now}</span>}
          {event.data_origin === 'mock' && (
            <span className="demo-badge caption" title="Демо-данные: событие из тестового набора">
              {T.card.demo}
            </span>
          )}
        </div>

        <h1 className="detail__title t-hero">{event.title}</h1>

        <div className="detail__when">
          <div className={`detail__dateplate${now ? ' detail__dateplate--now' : ''}`} aria-hidden="true">
            <span className="t-date-hero">{dayNumber(event.starts_at)}</span>
            <span className="caption">{monthShort(event.starts_at)}</span>
          </div>
          <div className="detail__when-text">
            <p className="detail__day ui">{fullDateLabel(event.starts_at)}</p>
            <p className="detail__time body tnum">
              {formatTimeRange(event.starts_at, event.ends_at)}
            </p>
          </div>
        </div>

        <div className="detail__plates">
          <span className={`plate plate--lg${event.is_free ? ' plate--free' : ''}`}>
            {event.price_display}
          </span>
          {event.age_limit && <span className="plate plate--lg plate--age">{event.age_limit}</span>}
          {event.distance_km != null && (
            <span className="plate plate--lg tnum">{formatKm(event.distance_km)}</span>
          )}
        </div>

        <section className="detail__block">
          <h2 className="detail__h t-section">{T.details.whereTitle}</h2>
          <p className="body">{event.venue_name ?? T.card.venueUnknown}</p>
          <p className="body muted">
            {event.address ?? T.details.addressUnknown}
            {event.city_name ? `, ${event.city_name}` : ''}
          </p>
        </section>

        {event.reason && (
          <section className="detail__block">
            <h2 className="detail__h t-section">{T.details.reasonTitle}</h2>
            <div className="note">
              <p className="note__text body">{event.reason}</p>
            </div>
          </section>
        )}

        {event.description && (
          <section className="detail__block">
            <h2 className="detail__h t-section">{T.details.descriptionTitle}</h2>
            <p className="detail__desc body-l">{event.description}</p>
          </section>
        )}

        {event.image_url && (
          <img className="detail__photo" src={event.image_url} alt={event.title} loading="lazy" />
        )}

        <p className="detail__source caption muted">
          {T.details.sourceLabel}: {event.provider}
        </p>
      </main>

      <div className="actionbar">
        <button
          type="button"
          className={`btn btn--ghost actionbar__fav${saved ? ' actionbar__fav--on' : ''}`}
          onClick={() => void fav.toggle(event)}
          aria-pressed={saved}
        >
          <Icon name={saved ? 'bookmark-filled' : 'bookmark'} size={20} />
        </button>
        {event.source_url ? (
          <button type="button" className="btn btn--lamp actionbar__buy" onClick={() => void onBuy()} disabled={opening}>
            {opening ? T.details.opening : event.is_free ? T.details.toSource : T.details.buy}
          </button>
        ) : (
          <button type="button" className="btn btn--lamp actionbar__buy" disabled>
            {T.details.noSource}
          </button>
        )}
      </div>
    </div>
  );
}

function DetailHeader({ onBack, right }: { onBack: () => void; right?: ReactNode }) {
  return (
    <header className="header header--detail">
      <button type="button" className="header__back" onClick={onBack}>
        <Icon name="chevron-left" size={20} />
        <span className="ui">{T.details.back}</span>
      </button>
      {right}
    </header>
  );
}
