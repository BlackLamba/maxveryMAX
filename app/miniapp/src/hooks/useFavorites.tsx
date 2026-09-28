/**
 * Закладки (избранное): GET/POST/DELETE /api/favorites?user_id=…
 *
 * user_id — из MAX initData (в браузере — стабильный dev-id).
 * Toggle — оптимистичный: иконка переключается сразу, при ошибке API
 * откатывается + баннер. Удаление 404 («нет такого события в избранном»)
 * считаем успехом — состояние уже совпало с сервером.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { ApiError, api } from '@/api/client';
import type { EventOut, FavoriteOut } from '@/types/api';
import { useMaxUI } from '@/components/MaxUIProvider';
import { useBanner } from '@/components/BannerHost';
import { haptic } from '@/utils/platform';
import { T } from '@/utils/texts';

export type FavoritesStatus = 'loading' | 'ready' | 'error';

interface FavoritesState {
  ids: Set<number>;
  items: FavoriteOut[];
  status: FavoritesStatus;
  has: (id: number) => boolean;
  toggle: (ev: EventOut) => Promise<void>;
  reload: () => Promise<void>;
  count: number;
}

const FavoritesCtx = createContext<FavoritesState | null>(null);

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const { userId } = useMaxUI();
  const banner = useBanner();
  const [ids, setIds] = useState<Set<number>>(new Set());
  const [items, setItems] = useState<FavoriteOut[]>([]);
  const [status, setStatus] = useState<FavoritesStatus>('loading');
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const reload = useCallback(async () => {
    if (!userId) return;
    setStatus('loading');
    try {
      const env = await api.favorites(userId);
      if (!mounted.current) return;
      setItems(env.items);
      setIds(new Set(env.items.map((i) => i.id)));
      setStatus('ready');
    } catch (err) {
      if (!mounted.current) return;
      if (err instanceof ApiError && err.status === 404) {
        setItems([]);
        setIds(new Set());
        setStatus('ready');
        return;
      }
      setStatus('error');
    }
  }, [userId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const toggle = useCallback(
    async (ev: EventOut) => {
      const removing = ids.has(ev.id);
      // оптимистично
      setIds((prev) => {
        const next = new Set(prev);
        if (removing) next.delete(ev.id);
        else next.add(ev.id);
        return next;
      });
      haptic('light');
      try {
        if (removing) {
          await api.removeFavorite(userId, ev.id);
        } else {
          await api.addFavorite(userId, ev.id);
        }
        banner.show(removing ? T.banner.favRemoved : T.banner.favAdded, 'ok');
        // список на экране «Закладки» должен остаться точным (added_at, порядок)
        await reload();
      } catch (err) {
        // откат
        setIds((prev) => {
          const next = new Set(prev);
          if (removing) next.add(ev.id);
          else next.delete(ev.id);
          return next;
        });
        if (err instanceof ApiError && err.status === 404 && removing) {
          banner.show(T.banner.favRemoved, 'ok');
          await reload();
          return;
        }
        banner.show(T.banner.favFailed, 'error');
      }
    },
    [ids, userId, banner, reload],
  );

  const has = useCallback((id: number) => ids.has(id), [ids]);

  const value = useMemo<FavoritesState>(
    () => ({ ids, items, status, has, toggle, reload, count: ids.size }),
    [ids, items, status, has, toggle, reload],
  );

  return <FavoritesCtx.Provider value={value}>{children}</FavoritesCtx.Provider>;
}

export function useFavorites(): FavoritesState {
  const ctx = useContext(FavoritesCtx);
  if (!ctx) throw new Error('useFavorites вне <FavoritesProvider>');
  return ctx;
}
