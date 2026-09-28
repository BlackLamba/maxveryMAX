/**
 * Экран 3 — Закладки (избранное): GET /api/favorites?user_id=…, снятие —
 * DELETE /api/favorites/{event_id}?user_id=… (через toggle провайдера).
 * Ближайшие события сверху (сортировка по starts_at на клиенте — API
 * возвращает по дате добавления).
 */
import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useFavorites } from '@/hooks/useFavorites';
import { TicketCard } from '@/components/TicketCard';
import { ErrorState, ListSkeleton } from '@/components/StateViews';
import { parseApiDate } from '@/utils/format';
import { useMaxUI } from '@/components/MaxUIProvider';
import { T } from '@/utils/texts';

export function Favorites() {
  const fav = useFavorites();
  const { userName } = useMaxUI();

  const sorted = useMemo(
    () =>
      [...fav.items].sort(
        (a, b) => parseApiDate(a.starts_at).getTime() - parseApiDate(b.starts_at).getTime(),
      ),
    [fav.items],
  );

  return (
    <div className="page page--favorites">
      <header className="header header--static">
        <h1 className="header__title t-section">
          {T.favorites.title}
          {fav.count > 0 && <span className="header__count caption tnum">{fav.count}</span>}
        </h1>
      </header>

      <main className="feed">
        {fav.status === 'loading' ? (
          <ListSkeleton count={3} />
        ) : fav.status === 'error' ? (
          <ErrorState onRetry={() => void fav.reload()} />
        ) : sorted.length === 0 ? (
          <div className="state">
            <h2 className="state__title t-hero">{T.favorites.emptyTitle}</h2>
            <p className="state__body body">
              {userName
                ? `${userName}, ${T.favorites.emptyBody[0].toLowerCase()}${T.favorites.emptyBody.slice(1)}`
                : T.favorites.emptyBody}
            </p>
            <Link to="/" className="btn btn--lamp state__action">
              {T.favorites.toFeed}
            </Link>
          </div>
        ) : (
          <div className="list">
            {sorted.map((ev) => (
              <TicketCard key={ev.id} ev={ev} showCity />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}