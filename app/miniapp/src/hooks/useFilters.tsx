/**
 * Контейнер фильтров ленты.
 *
 * Порядок инициализации (задача, п.5.6): deep link от бота → сохранённые
 * предпочтения (GET /api/preferences) → дефолты. Первый запрос /api/events
 * уходит только когда оба источника применены (флаг ready) — никаких
 * «сначала дефолтный запрос, потом перерисовка».
 *
 * Инварианты контракта (schemas/events.py):
 * - time_from/time_to — только при date_from === date_to (один день);
 * - radius_km и sort=distance — только при lat+lon.
 * UI не даёт собрать невалидную комбинацию, билдер query — перестраховывается.
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
import { CATEGORY_SLUGS, type CategorySlug } from '@shared/categories';
import { api } from '@/api/client';
import { useRefs, type RefsState } from '@/hooks/useRefs';
import { useMaxUI } from '@/components/MaxUIProvider';
import { readLaunchParams, type LaunchFilters } from '@/utils/launchParams';
import type { CityOut, EventsQuery, SortOption } from '@/types/api';

export interface ActiveFilters {
  cityId: number | null;
  categories: CategorySlug[];
  dateFrom: string | null;
  dateTo: string | null;
  timeFrom: string | null;
  timeTo: string | null;
  priceMax: number | null;
  isFree: boolean;
  lat: number | null;
  lon: number | null;
  radiusKm: number | null;
  sort: SortOption;
}

const DEFAULTS: ActiveFilters = {
  cityId: null,
  categories: [],
  dateFrom: null,
  dateTo: null,
  timeFrom: null,
  timeTo: null,
  priceMax: null,
  isFree: false,
  lat: null,
  lon: null,
  radiusKm: null,
  sort: 'relevance',
};

interface FiltersState extends RefsState {
  filters: ActiveFilters;
  /** deep link + предпочтения применены, можно делать первый запрос */
  ready: boolean;
  setCityId: (id: number | null) => void;
  toggleCategory: (slug: CategorySlug) => void;
  clearCategories: () => void;
  selectDay: (key: string | null) => void;
  setDateRange: (from: string | null, to: string | null) => void;
  setTimeWindow: (from: string | null, to: string | null) => void;
  setBudget: (max: number | null) => void;
  setFreeOnly: (v: boolean) => void;
  setGeo: (lat: number | null, lon: number | null) => void;
  setRadius: (km: number | null) => void;
  setSort: (s: SortOption) => void;
  resetSheet: () => void;
  resetAll: () => void;
  /** число активных фильтров из bottom-sheet (бейдж на кнопке) */
  sheetCount: number;
  /** собрать query для GET /api/events (с защитой от невалидных комбинаций) */
  toQuery: (extra?: { limit?: number; offset?: number }) => EventsQuery;
  /** город выбран из deep link'а slug'ом — для отображения */
  cityById: (id: number | null) => CityOut | undefined;
}

const FiltersCtx = createContext<FiltersState | null>(null);

export function FiltersProvider({ children }: { children: ReactNode }) {
  const { userId } = useMaxUI();
  const refs = useRefs();
  const [filters, setFilters] = useState<ActiveFilters>(DEFAULTS);

  const launch = useRef<LaunchFilters | null>(null);
  if (launch.current === null) launch.current = readLaunchParams();

  const [citiesResolved, setCitiesResolved] = useState(false);
  const [prefsResolved, setPrefsResolved] = useState(false);
  const prefsRequested = useRef(false);

  // --- 1. Deep link: город (slug → id, когда справочник загружен) -----------
  useEffect(() => {
    if (refs.citiesLoading) return;
    const lc = launch.current?.city;
    if (lc) {
      const numeric = Number(lc);
      const byId = Number.isFinite(numeric)
        ? refs.cities.find((c) => c.id === numeric)
        : undefined;
      const bySlug = refs.cities.find((c) => c.slug === lc.toLowerCase());
      const resolved = byId ?? bySlug;
      if (resolved) setFilters((f) => (f.cityId === null ? { ...f, cityId: resolved.id } : f));
    }
    setCitiesResolved(true);
  }, [refs.citiesLoading, refs.cities]);

  // Немедленно применяем то, что не требует справочников.
  useEffect(() => {
    const l = launch.current;
    if (!l) return;
    setFilters((f) => ({
      ...f,
      categories: l.categories ?? f.categories,
      dateFrom: l.dateFrom ?? f.dateFrom,
      dateTo: l.dateTo ?? f.dateTo,
      timeFrom: l.timeFrom ?? f.timeFrom,
      timeTo: l.timeTo ?? f.timeTo,
      priceMax: l.priceMax ?? f.priceMax,
      isFree: l.isFree ?? f.isFree,
      lat: l.lat ?? f.lat,
      lon: l.lon ?? f.lon,
      radiusKm: l.radiusKm ?? f.radiusKm,
      sort: l.sort ?? f.sort,
    }));
  }, []);

  // --- 2. Сохранённые предпочтения (только раз, заполняют пустое) ----------
  useEffect(() => {
    if (prefsRequested.current || !userId) return;
    prefsRequested.current = true;
    api
      .preferences(userId)
      .then((p) => {
        if (!p.saved) return;
        setFilters((f) => {
          const next = { ...f };
          const l = launch.current;
          // deep link приоритетнее предпочтений — заполняем только пустое
          if (next.categories.length === 0 && !l?.categories && p.categories.length > 0) {
            next.categories = p.categories.filter((c): c is CategorySlug =>
              (CATEGORY_SLUGS as readonly string[]).includes(c),
            );
          }
          if (next.priceMax === null && l?.priceMax === undefined) next.priceMax = p.price_max;
          if (
            next.radiusKm === null &&
            l?.radiusKm === undefined &&
            p.radius_km !== null &&
            next.lat !== null &&
            next.lon !== null
          ) {
            next.radiusKm = p.radius_km;
          }
          return next;
        });
      })
      .catch(() => {
        /* нет сохранённых — работаем с дефолтами */
      })
      .finally(() => setPrefsResolved(true));
  }, [userId]);

  const ready = citiesResolved && prefsResolved;

  // --- setters --------------------------------------------------------------
  const patch = useCallback((p: Partial<ActiveFilters>) => {
    setFilters((f) => ({ ...f, ...p }));
  }, []);

  const setCityId = useCallback((id: number | null) => patch({ cityId: id }), [patch]);

  const toggleCategory = useCallback((slug: CategorySlug) => {
    setFilters((f) => ({
      ...f,
      categories: f.categories.includes(slug)
        ? f.categories.filter((c) => c !== slug)
        : [...f.categories, slug],
    }));
  }, []);

  const clearCategories = useCallback(() => patch({ categories: [] }), [patch]);

  const selectDay = useCallback(
    (key: string | null) => {
      setFilters((f) => {
        const next = { ...f, dateFrom: key, dateTo: key };
        // временное окно живет только внутри одного дня
        if (key === null) {
          next.timeFrom = null;
          next.timeTo = null;
        }
        return next;
      });
    },
    [],
  );

  const setDateRange = useCallback(
    (from: string | null, to: string | null) => {
      setFilters((f) => {
        const next = { ...f, dateFrom: from, dateTo: to };
        if (from !== to) {
          next.timeFrom = null;
          next.timeTo = null;
        }
        return next;
      });
    },
    [],
  );

  const setTimeWindow = useCallback(
    (from: string | null, to: string | null) => {
      setFilters((f) =>
        f.dateFrom && f.dateFrom === f.dateTo ? { ...f, timeFrom: from, timeTo: to } : f,
      );
    },
    [],
  );

  const setBudget = useCallback((max: number | null) => patch({ priceMax: max }), [patch]);
  const setFreeOnly = useCallback((v: boolean) => patch({ isFree: v }), [patch]);

  const setGeo = useCallback(
    (lat: number | null, lon: number | null) => {
      setFilters((f) => ({
        ...f,
        lat,
        lon,
        radiusKm: lat === null || lon === null ? null : f.radiusKm,
        // sort=distance без координат невалиден (400) — откатываемся
        sort: lat === null && f.sort === 'distance' ? 'relevance' : f.sort,
      }));
    },
    [],
  );

  const setRadius = useCallback((km: number | null) => patch({ radiusKm: km }), [patch]);

  const setSort = useCallback(
    (s: SortOption) => {
      setFilters((f) => (s === 'distance' && (f.lat === null || f.lon === null) ? f : { ...f, sort: s }));
    },
    [],
  );

  const resetSheet = useCallback(
    () => patch({ timeFrom: null, timeTo: null, priceMax: null, isFree: false, radiusKm: null }),
    [patch],
  );

  const resetAll = useCallback(
    () =>
      setFilters((f) => ({
        ...DEFAULTS,
        cityId: f.cityId, // город — контекст пользователя, не «фильтр»
        lat: f.lat,
        lon: f.lon,
      })),
    [],
  );

  const sheetCount =
    (filters.timeFrom || filters.timeTo ? 1 : 0) +
    (filters.priceMax !== null ? 1 : 0) +
    (filters.isFree ? 1 : 0) +
    (filters.radiusKm !== null && filters.lat !== null ? 1 : 0);

  const toQuery = useCallback(
    (extra?: { limit?: number; offset?: number }): EventsQuery => {
      const q: EventsQuery = { user_id: userId };
      if (filters.cityId !== null) q.city_id = filters.cityId;
      if (filters.dateFrom) q.date_from = filters.dateFrom;
      if (filters.dateTo) q.date_to = filters.dateTo;
      const singleDay = filters.dateFrom !== null && filters.dateFrom === filters.dateTo;
      if (singleDay) {
        if (filters.timeFrom) q.time_from = filters.timeFrom;
        if (filters.timeTo) q.time_to = filters.timeTo;
      }
      if (filters.categories.length > 0) q.category = filters.categories;
      if (filters.priceMax !== null) q.price_max = filters.priceMax;
      if (filters.isFree) q.is_free = true;
      if (filters.lat !== null && filters.lon !== null) {
        q.lat = filters.lat;
        q.lon = filters.lon;
        if (filters.radiusKm !== null) q.radius_km = filters.radiusKm;
        if (filters.sort === 'distance') q.sort = 'distance';
      }
      if (filters.sort !== 'distance') q.sort = filters.sort;
      if (extra?.limit) q.limit = extra.limit;
      if (extra?.offset) q.offset = extra.offset;
      return q;
    },
    [filters, userId],
  );

  const cityById = useCallback(
    (id: number | null) => (id === null ? undefined : refs.cities.find((c) => c.id === id)),
    [refs.cities],
  );

  const value = useMemo<FiltersState>(
    () => ({
      ...refs,
      filters,
      ready,
      setCityId,
      toggleCategory,
      clearCategories,
      selectDay,
      setDateRange,
      setTimeWindow,
      setBudget,
      setFreeOnly,
      setGeo,
      setRadius,
      setSort,
      resetSheet,
      resetAll,
      sheetCount,
      toQuery,
      cityById,
    }),
    [
      refs,
      filters,
      ready,
      setCityId,
      toggleCategory,
      clearCategories,
      selectDay,
      setDateRange,
      setTimeWindow,
      setBudget,
      setFreeOnly,
      setGeo,
      setRadius,
      setSort,
      resetSheet,
      resetAll,
      sheetCount,
      toQuery,
      cityById,
    ],
  );

  return <FiltersCtx.Provider value={value}>{children}</FiltersCtx.Provider>;
}

export function useFiltersState(): FiltersState {
  const ctx = useContext(FiltersCtx);
  if (!ctx) throw new Error('useFiltersState вне <FiltersProvider>');
  return ctx;
}
