/**
 * Строка активных фильтров из bottom-sheet (+ диапазон дат из deep link'а):
 * каждый фильтр виден и снимается одним тапом. Пусто — строки нет.
 * Deep link не прячет параметры: что пришло от бота, то видно пользователю.
 */
import type { ActiveFilters } from '@/hooks/useFilters';
import { formatRub, shortRangeLabel } from '@/utils/format';
import { Icon } from '@/components/Icon';
import { T } from '@/utils/texts';

interface Props {
  filters: ActiveFilters;
  onClearDates: () => void;
  onClearTime: () => void;
  onClearBudget: () => void;
  onClearFree: () => void;
  onClearRadius: () => void;
  onResetAll: () => void;
}

interface ChipDef {
  key: string;
  label: string;
  onClear: () => void;
}

export function ActiveFilterChips({
  filters,
  onClearDates,
  onClearTime,
  onClearBudget,
  onClearFree,
  onClearRadius,
  onResetAll,
}: Props) {
  const chips: ChipDef[] = [];

  // диапазон дат показываем чипом, только если это НЕ один день
  // (один день виден в дата-линейке)
  if (filters.dateFrom && filters.dateTo && filters.dateFrom !== filters.dateTo) {
    chips.push({
      key: 'dates',
      label: shortRangeLabel(filters.dateFrom, filters.dateTo),
      onClear: onClearDates,
    });
  }
  if (filters.timeFrom || filters.timeTo) {
    chips.push({
      key: 'time',
      label: `${filters.timeFrom ?? '00:00'}–${filters.timeTo ?? '23:59'}`,
      onClear: onClearTime,
    });
  }
  if (filters.priceMax !== null) {
    chips.push({ key: 'budget', label: `до ${formatRub(filters.priceMax)}`, onClear: onClearBudget });
  }
  if (filters.isFree) {
    chips.push({ key: 'free', label: T.filters.freeOnly.toLowerCase(), onClear: onClearFree });
  }
  if (filters.radiusKm !== null && filters.lat !== null) {
    chips.push({
      key: 'radius',
      label: `в пределах ${filters.radiusKm} км`,
      onClear: onClearRadius,
    });
  }

  if (chips.length === 0) return null;

  return (
    <div className="active-chips" aria-label={T.filters.activePrefix}>
      {chips.map((c) => (
        <button key={c.key} type="button" className="active-chip caption" onClick={c.onClear}>
          {c.label}
          <Icon name="close" size={12} />
          <span className="visually-hidden">— снять фильтр</span>
        </button>
      ))}
      {chips.length >= 2 && (
        <button type="button" className="active-chip active-chip--reset caption" onClick={onResetAll}>
          {T.filters.clearAll}
        </button>
      )}
    </div>
  );
}
