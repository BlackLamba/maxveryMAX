/**
 * Справочники: города (GET /api/cities) и категории (GET /api/categories).
 * Категории дублируются фолбэком из shared/categories.ts, если запрос не
 * прошёл — лента остаётся фильтруемой даже при проблемах со справочниками.
 */
import { useEffect, useState } from 'react';
import { api } from '@/api/client';
import type { CityOut } from '@/types/api';
import { CATEGORY_SLUGS, CATEGORY_NAMES, type CategorySlug } from '@shared/categories';

export interface RefsState {
  cities: CityOut[];
  categories: Array<{ slug: CategorySlug; name: string }>;
  citiesLoading: boolean;
}

const SHARED_CATEGORIES = CATEGORY_SLUGS.map((slug) => ({ slug, name: CATEGORY_NAMES[slug] }));

export function useRefs(): RefsState {
  const [cities, setCities] = useState<CityOut[]>([]);
  const [categories, setCategories] = useState(SHARED_CATEGORIES);
  const [citiesLoading, setCitiesLoading] = useState(true);

  useEffect(() => {
    const ac = new AbortController();

    api
      .cities(ac.signal)
      .then((env) => setCities(env.items))
      .catch(() => {
        /* селектор города останется с опцией «Все города» */
      })
      .finally(() => {
        if (!ac.signal.aborted) setCitiesLoading(false);
      });

    api
      .categories(ac.signal)
      .then((env) => {
        if (env.items.length > 0) {
          // порядок — из API; подписи — из shared (ас-is, не выдумываем)
          setCategories(
            env.items.map((c) => ({ slug: c.slug, name: CATEGORY_NAMES[c.slug] ?? c.name })),
          );
        }
      })
      .catch(() => {
        /* фолбэк shared уже в состоянии */
      });

    return () => ac.abort();
  }, []);

  return { cities, categories, citiesLoading };
}
