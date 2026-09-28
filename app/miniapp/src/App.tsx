/**
 * Корень приложения: провайдеры + маршруты (HashRouter из main.tsx).
 *
 * Слои контекста (снаружи внутрь):
 * MaxUI (тема, user_id из MAX initData) → Filters (deep link → preferences)
 * → Banner (сообщения о действиях) → Favorites (нужен user_id и баннер).
 *
 * /api/health проверяется при старте: 'down' — отдельный экран «Сервис
 * афиши не отвечает» (не спиннер), 'degraded' — баннер сверху.
 */
import { useEffect, useRef } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { MaxUIProvider } from '@/components/MaxUIProvider';
import { FiltersProvider } from '@/hooks/useFilters';
import { BannerProvider } from '@/components/BannerHost';
import { FavoritesProvider } from '@/hooks/useFavorites';
import { BottomNav } from '@/components/BottomNav';
import { BackendDownState } from '@/components/StateViews';
import { EventsList } from '@/pages/EventsList';
import { EventDetails } from '@/pages/EventDetails';
import { Favorites } from '@/pages/Favorites';
import { useHealth } from '@/hooks/useHealth';
import { readLaunchParams } from '@/utils/launchParams';
import { T } from '@/utils/texts';

function Shell() {
  const { health, checking, recheck } = useHealth();
  const location = useLocation();
  const navigate = useNavigate();
  const launchHandled = useRef(false);

  // Deep link на конкретное событие (?event=123 / startapp=event=123)
  useEffect(() => {
    if (launchHandled.current) return;
    launchHandled.current = true;
    const launch = readLaunchParams();
    if (launch.eventId) navigate(`/event/${launch.eventId}`, { replace: true });
  }, [navigate]);

  if (health === 'down') {
    return <BackendDownState onRetry={recheck} checking={checking} />;
  }

  const isDetail = location.pathname.startsWith('/event/');

  return (
    <div className="shell">
      {health === 'degraded' && (
        <div className="degraded" role="status">
          {T.degraded}
        </div>
      )}

      <Routes>
        <Route path="/" element={<EventsList />} />
        <Route path="/event/:id" element={<EventDetails />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="*" element={<EventsList />} />
      </Routes>

      {!isDetail && <BottomNav />}
    </div>
  );
}

export default function App() {
  return (
    <MaxUIProvider>
      <FiltersProvider>
        <BannerProvider>
          <FavoritesProvider>
            <Shell />
          </FavoritesProvider>
        </BannerProvider>
      </FiltersProvider>
    </MaxUIProvider>
  );
}
