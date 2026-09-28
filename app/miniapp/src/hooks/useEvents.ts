/**
 * Лента событий: GET /api/events с фильтрами + пагинация «Показать ещё».
 * Конверт {items,total,hint}: hint показываем дословно в EmptyState.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, api } from '@/api/client';
import type { EventsQuery, EventOut } from '@/types/api';

export type EventsStatus = 'idle' | 'loading' | 'loading-more' | 'ready' | 'error';

export interface EventsState {
  status: EventsStatus;
  items: EventOut[];
  total: number;
  hint: string | null;
  error: ApiError | null;
}

const PAGE = 20;

function isAbort(e: unknown): boolean {
  return e instanceof Error && e.name === 'AbortError';
}

function toApiError(e: unknown): ApiError {
  return e instanceof ApiError
    ? e
    : new ApiError(0, 'network_error', 'нет соединения', undefined, true);
}

export function useEvents(query: EventsQuery, enabled: boolean) {
  const key = JSON.stringify(query);
  const keyRef = useRef(key);
  keyRef.current = key;

  const [state, setState] = useState<EventsState>({
    status: 'idle',
    items: [],
    total: 0,
    hint: null,
    error: null,
  });
  const [nonce, setNonce] = useState(0);
  const itemsRef = useRef<EventOut[]>([]);
  itemsRef.current = state.items;

  useEffect(() => {
    if (!enabled) return;
    const ac = new AbortController();
    setState((s) => ({ ...s, status: 'loading', error: null }));
    api
      .events({ ...query, limit: PAGE, offset: 0 }, ac.signal)
      .then((env) => {
        setState({ status: 'ready', items: env.items, total: env.total, hint: env.hint, error: null });
      })
      .catch((err: unknown) => {
        if (isAbort(err) || ac.signal.aborted) return;
        setState({ status: 'error', items: [], total: 0, hint: null, error: toApiError(err) });
      });
    return () => ac.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, enabled, nonce]);

  const refetch = useCallback(() => setNonce((n) => n + 1), []);

  const loadMore = useCallback(async () => {
    const requestKey = keyRef.current;
    const offset = itemsRef.current.length;
    setState((s) => ({ ...s, status: 'loading-more', error: null }));
    try {
      const env = await api.events({ ...query, limit: PAGE, offset });
      // фильтры сменились, пока грузили следующую страницу, — результат устарел
      if (keyRef.current !== requestKey) return;
      setState((s) => ({
        ...s,
        status: 'ready',
        items: [...s.items, ...env.items],
        total: env.total,
        hint: env.hint,
      }));
    } catch (err: unknown) {
      if (isAbort(err) || keyRef.current !== requestKey) return;
      // список сохраняем, ошибку показываем у кнопки «ещё»
      setState((s) => ({ ...s, status: 'ready', error: toApiError(err) }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { ...state, refetch, loadMore, page: PAGE };
}
