/**
 * Строка управления лентой: чипы категорий (скроллятся), кнопка фильтров
 * с бейджем активных, селект сортировки. Sticky под шапкой.
 *
 * Категории — из /api/categories (фолбэк shared/categories.ts), подписи —
 * CATEGORY_NAMES as-is. Мультивыбор: ?category=a&category=b.
 */
import type { CategorySlug } from '@shared/categories';
import type { SortOption } from '@/types/api';
import { Icon } from '@/components/Icon';
import { T } from '@/utils/texts';

interface Props {
  categories: Array<{ slug: CategorySlug; name: string }>;
  selected: CategorySlug[];
  onToggle: (slug: CategorySlug) => void;
  onClear: () => void;
  sort: SortOption;
  onSort: (s: SortOption) => void;
  hasGeo: boolean;
  sheetCount: number;
  onOpenFilters: () => void;
}

const SORTS: Array<{ value: SortOption; label: string; needsGeo?: boolean }> = [
  { value: 'relevance', label: T.sort.relevance },
  { value: 'date_asc', label: T.sort.date_asc },
  { value: 'price_asc', label: T.sort.price_asc },
  { value: 'price_desc', label: T.sort.price_desc },
  { value: 'distance', label: T.sort.distance, needsGeo: true },
];

export function FeedControls({
  categories,
  selected,
  onToggle,
  onClear,
  sort,
  onSort,
  hasGeo,
  sheetCount,
  onOpenFilters,
}: Props) {
  return (
    <div className="controls">
      <div className="controls__chips" role="group" aria-label="Категории">
        <button
          type="button"
          className={`chip ui${selected.length === 0 ? ' chip--on' : ''}`}
          onClick={onClear}
          aria-pressed={selected.length === 0}
        >
          {T.feed.allCategories}
        </button>
        {categories.map((c) => {
          const on = selected.includes(c.slug);
          return (
            <button
              key={c.slug}
              type="button"
              className={`chip ui${on ? ' chip--on' : ''}`}
              onClick={() => onToggle(c.slug)}
              aria-pressed={on}
            >
              {c.name}
            </button>
          );
        })}
      </div>

      <div className="controls__side">
        <button
          type="button"
          className={`ctl-btn${sheetCount > 0 ? ' ctl-btn--active' : ''}`}
          onClick={onOpenFilters}
          aria-label={T.feed.filters}
          title={T.feed.filters}
        >
          <Icon name="sliders" size={20} />
          {sheetCount > 0 && <span className="ctl-btn__badge caption tnum">{sheetCount}</span>}
        </button>

        <div className="sort">
          <select
            className="sort__select ui"
            value={sort}
            onChange={(e) => onSort(e.target.value as SortOption)}
            aria-label={T.sort.label}
          >
            {SORTS.filter((s) => !s.needsGeo || hasGeo).map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <Icon name="chevron-down" size={14} className="sort__chev" />
        </div>
      </div>
    </div>
  );
}
