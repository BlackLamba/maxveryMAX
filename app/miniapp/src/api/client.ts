/**
 * Единый API-клиент к backend/ (README: miniapp ходит ТОЛЬКО в backend).
 *
 * Базовый URL — из VITE_API_URL; по умолчанию пусто → относительный /api
 * (dev: прокси Vite на backend, prod: прокси nginx). Никаких захардкоженных
 * localhost в браузерном коде (README 5.4).
 */
import type {
  CategorySlug,
  CityOut,
  Envelope,
  EventOut,
  EventsQuery,
  FavoriteOut,
  HealthOut,
  PreferenceIn,
  PreferenceOut,
} from '@/types/api';

const BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '');

export type ApiErrorCode =
  | 'network_error'
  | 'not_found'
  | 'validation_error'
  | 'server_error'
  | string;

/** Ошибка запроса в едином формате: код из error.code бэкенда или network_error. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: ApiErrorCode;
  readonly details: unknown;
  /** true — запрос не дошёл до сервера (offline / backend недоступен) */
  readonly networkError: boolean;

  constructor(
    status: number,
    code: ApiErrorCode,
    message: string,
    details?: unknown,
    networkError = false,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.networkError = networkError;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
  } catch (e) {
    // отмена запроса — не сетевая ошибка, пробрасываем как есть
    if (e instanceof Error && e.name === 'AbortError') throw e;
    throw new ApiError(0, 'network_error', 'нет соединения', undefined, true);
  }

  if (!res.ok) {
    let code: ApiErrorCode = res.status === 404 ? 'not_found' : 'server_error';
    let message = `сервис ответил ошибкой (${res.status})`;
    let details: unknown;
    try {
      const body = (await res.json()) as {
        error?: { code?: string; message?: string; details?: unknown };
      };
      if (body?.error) {
        code = body.error.code ?? code;
        message = body.error.message ?? message;
        details = body.error.details;
      }
    } catch {
      /* тело не JSON — оставляем дефолт */
    }
    throw new ApiError(res.status, code, message, details);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/**
 * Query для GET /api/events. Категория — повторяемый параметр
 * (?category=concert&category=theater, см. комментарий в backend/api/events.py);
 * пустые значения не отправляем.
 */
export function buildEventsQuery(q: EventsQuery): string {
  const p = new URLSearchParams();
  const set = (k: string, v: string | number | boolean | undefined | null) => {
    if (v !== undefined && v !== null && v !== '') p.set(k, String(v));
  };
  set('city_id', q.city_id);
  set('date_from', q.date_from);
  set('date_to', q.date_to);
  set('time_from', q.time_from);
  set('time_to', q.time_to);
  for (const c of q.category ?? []) p.append('category', c);
  set('price_max', q.price_max);
  if (q.is_free === true) p.set('is_free', 'true');
  set('lat', q.lat);
  set('lon', q.lon);
  set('radius_km', q.radius_km);
  set('sort', q.sort && q.sort !== 'relevance' ? q.sort : undefined);
  set('limit', q.limit);
  set('offset', q.offset && q.offset > 0 ? q.offset : undefined);
  set('user_id', q.user_id);
  const s = p.toString();
  return s ? `?${s}` : '';
}

export const api = {
  /** health-check при старте — для состояния «сервис недоступен» */
  health(signal?: AbortSignal): Promise<HealthOut> {
    return request<HealthOut>('/health', { signal });
  },

  cities(signal?: AbortSignal): Promise<Envelope<CityOut>> {
    return request<Envelope<CityOut>>('/cities', { signal });
  },

  categories(signal?: AbortSignal): Promise<Envelope<{ id: number; slug: CategorySlug; name: string }>> {
    return request('/categories', { signal });
  },

  events(q: EventsQuery, signal?: AbortSignal): Promise<Envelope<EventOut>> {
    return request<Envelope<EventOut>>(`/events${buildEventsQuery(q)}`, { signal });
  },

  event(id: number, q: EventsQuery = {}, signal?: AbortSignal): Promise<EventOut> {
    return request<EventOut>(`/events/${id}${buildEventsQuery(q)}`, { signal });
  },

  /** лог перехода на источник — ОБЯЗАТЕЛЬНО до открытия source_url */
  logClick(eventId: number, userId: string | null, meta?: Record<string, unknown>): Promise<{ ok: boolean }> {
    return request(`/events/${eventId}/click`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId ?? undefined, meta }),
    });
  },

  favorites(userId: string, signal?: AbortSignal): Promise<Envelope<FavoriteOut>> {
    return request<Envelope<FavoriteOut>>(`/favorites?user_id=${encodeURIComponent(userId)}`, {
      signal,
    });
  },

  addFavorite(userId: string, eventId: number): Promise<{ ok: boolean }> {
    return request('/favorites', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, event_id: eventId }),
    });
  },

  removeFavorite(userId: string, eventId: number): Promise<{ ok: boolean }> {
    return request(`/favorites/${eventId}?user_id=${encodeURIComponent(userId)}`, {
      method: 'DELETE',
    });
  },

  preferences(userId: string, signal?: AbortSignal): Promise<PreferenceOut> {
    return request<PreferenceOut>(`/preferences?user_id=${encodeURIComponent(userId)}`, {
      signal,
    });
  },

  savePreferences(body: PreferenceIn): Promise<PreferenceOut> {
    return request('/preferences', { method: 'POST', body: JSON.stringify(body) });
  },
};
