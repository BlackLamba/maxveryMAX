/**
 * Экран 1 — Лента событий (задача п.5.1).
 * Порядок осей: когда (дата-линейка) → что (чипы категорий) → за сколько
 * (bottom-sheet). Список — рулон билетов. Все данные — GET /api/events,
 * справочники — /api/cities, /api/categories. Пусто → hint из конверта.
 */
import { useMemo, useState } from 'react';
import { useFiltersState } from '@/hooks/useFilters';
import { useEvents } from '@/hooks/useEvents';
import { TicketCard } from '@/components/TicketCard';
import { ListHeader } from '@/components/ListHeader';
import { DateRuler } from '@/components/DateRuler';
import { FeedControls } from '@/components/FeedControls';
import { ActiveFilterChips } from '@/components/ActiveFilterChips';
import { FilterSheet } from '@/components/FilterSheet';
import { EmptyState, ErrorState, ListSkeleton } from '@/components/StateViews';
import { eventsWord } from '@/utils/format';
import { T } from '@/utils/texts';

export function EventsList() {
  const F = useFiltersState();
  const [sheetOpen, setSheetOpen] = useState(false);

  const query = useMemo(() => F.toQuery(), [F.toQuery]);
  const events = useEvents(query, F.ready);

  const showCity = F.filters.cityId === null;
  const hasGeo = F.filters.lat !== null && F.filters.lon !== null;

  const applySheet = (d: {
    isFree: boolean;
    priceMax: number | null;
    timeFrom: string | null;
    timeTo: string | null;
    lat: number | null;
    lon: number | null;
    radiusKm: number | null;
  }) => {
    F.setFreeOnly(d.isFree);
    F.setBudget(d.priceMax);
    F.setTimeWindow(d.timeFrom, d.timeTo);
    if (d.lat !== null && d.lon !== null) {
      F.setGeo(d.lat, d.lon);
      F.setRadius(d.radiusKm);
    } else if (F.filters.lat !== null && d.lat === null) {
      F.setGeo(null, null);
    } else {
      F.setRadius(d.radiusKm);
    }
    setSheetOpen(false);
  };

  return (
    <div className="page page--list">
      <ListHeader cities={F.cities} cityId={F.filters.cityId} onCity={F.setCityId} />

      <DateRuler
        dateFrom={F.filters.dateFrom}
        dateTo={F.filters.dateTo}
        onSelect={F.selectDay}
      />

      <FeedControls
        categories={F.categories}
        selected={F.filters.categories}
        onToggle={F.toggleCategory}
        onClear={F.clearCategories}
        sort={F.filters.sort}
        onSort={F.setSort}
        hasGeo={hasGeo}
        sheetCount={F.sheetCount}
        onOpenFilters={() => setSheetOpen(true)}
      />

      <ActiveFilterChips
        filters={F.filters}
        onClearDates={() => F.setDateRange(null, null)}
        onClearTime={() => F.setTimeWindow(null, null)}
        onClearBudget={() => F.setBudget(null)}
        onClearFree={() => F.setFreeOnly(false)}
        onClearRadius={() => F.setRadius(null)}
        onResetAll={F.resetAll}
      />

      <main className="feed">
        {!F.ready || events.status === 'loading' ? (
          <ListSkeleton />
        ) : events.status === 'error' ? (
          <ErrorState error={events.error} onRetry={events.refetch} />
        ) : events.status === 'ready' && events.total === 0 ? (
          <EmptyState hint={events.hint} onReset={F.resetAll} />
        ) : (
          <>
            {events.status === 'ready' && events.total > 0 && (
              <p className="feed__count caption muted tnum">
                {T.feed.found(eventsWord(events.total))}
              </p>
            )}
            <div className="list">
              {events.items.map((ev) => (
                <TicketCard key={ev.id} ev={ev} showCity={showCity} />
              ))}
            </div>

            {events.items.length < events.total && (
              <div className="feed__more">
                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={() => void events.loadMore()}
                  disabled={events.status === 'loading-more'}
                >
                  {events.status === 'loading-more' ? 'Загружаем…' : T.feed.showMore}
                </button>
                {events.error && (
                  <p className="feed__more-error caption">{T.error.networkBody}</p>
                )}
              </div>
            )}
          </>
        )}
      </main>

      <FilterSheet
        open={sheetOpen}
        filters={F.filters}
        onClose={() => setSheetOpen(false)}
        onApply={applySheet}
      />
    </div>
  );
}
