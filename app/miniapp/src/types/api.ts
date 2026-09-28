/**
 * Типы API — синхронизированы с backend/app/schemas (events.py, user.py,
 * common.py). Источник истины — бэкенд; меняем здесь только вместе с ним.
 */
import type { CategorySlug } from '@shared/categories';

export type { CategorySlug };

/** GET /api/events?sort=… (SortOption в schemas/events.py) */
export type SortOption =
  | 'relevance'
  | 'date_asc'
  | 'price_asc'
  | 'price_desc'
  | 'distance';

/** Карточка события (EventOut). Даты — строки naive UTC из API (см. utils/format.ts). */
export interface EventOut {
  id: number;
  title: string;
  description: string;
  category: CategorySlug | string;
  category_name: string;
  city_id: number;
  city_slug: string;
  city_name: string;
  venue_name: string | null;
  address: string | null;
  lat: number | null;
  lon: number | null;
  /** только когда у запроса были координаты */
  distance_km: number | null;
  starts_at: string;
  ends_at: string | null;
  price_min: number | null;
  price_max: number | null;
  is_free: boolean;
  /** готовая строка цены — показываем as-is, не пересобираем из min/max */
  price_display: string;
  age_limit: string | null;
  image_url: string | null;
  source_url: string | null;
  /** человекочитаемое имя провайдера (уже преобразовано бэкендом) */
  provider: string;
  /** mock | live. mock ОБЯЗАН показываться как «демо-данные» */
  data_origin: 'mock' | 'live' | string;
  quality_score: number;
  updated_at: string;
  /** «почему подходит» — показываем как есть */
  reason: string | null;
  score: number | null;
}

/** GET /api/favorites — FavoriteOut = EventOut + added_at */
export interface FavoriteOut extends EventOut {
  added_at: string;
}

export interface CityOut {
  id: number;
  slug: string;
  name: string;
  lat: number | null;
  lon: number | null;
}

export interface CategoryOut {
  id: number;
  slug: CategorySlug;
  name: string;
}

/** Единый конверт списковых эндпоинтов; hint приходит только при total === 0. */
export interface Envelope<T> {
  items: T[];
  total: number;
  hint: string | null;
}

/** Единый формат ошибки (schemas/common.py) */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

/** GET /api/health */
export interface HealthOut {
  status: 'ok' | 'degraded' | string;
  db: 'ok' | 'error' | string;
  service: string;
  version: string;
}

/** GET/POST /api/preferences */
export interface PreferenceOut {
  user_id: string;
  categories: string[];
  price_max: number | null;
  radius_km: number | null;
  saved: boolean;
  updated_at: string | null;
}

export interface PreferenceIn {
  user_id: string;
  categories: CategorySlug[];
  price_max: number | null;
  radius_km: number | null;
}

/** Query-параметры GET /api/events (EventFilters как query). */
export interface EventsQuery {
  city_id?: number;
  date_from?: string; // YYYY-MM-DD (локальная дата города)
  date_to?: string;
  time_from?: string; // HH:MM (только при date_from === date_to!)
  time_to?: string;
  category?: CategorySlug[];
  price_max?: number;
  is_free?: boolean;
  lat?: number;
  lon?: number;
  radius_km?: number;
  sort?: SortOption;
  limit?: number;
  offset?: number;
  user_id?: string;
}
