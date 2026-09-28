/**
 * Шапка ленты (sticky): селектор города, живая дата, переключатель темы.
 * Город — контекст пользователя («в моём городе»), не один из фильтров:
 * живёт в шапке, а не в bottom-sheet.
 */
import type { CityOut } from '@/types/api';
import { useMaxUI } from '@/components/MaxUIProvider';
import { Icon } from '@/components/Icon';
import { dayLabelKey, todayKey } from '@/utils/format';
import { T } from '@/utils/texts';

interface Props {
  cities: CityOut[];
  cityId: number | null;
  onCity: (id: number | null) => void;
}

export function ListHeader({ cities, cityId, onCity }: Props) {
  const { theme, toggleTheme } = useMaxUI();

  return (
    <header className="header">
      <div className="header__city">
        <Icon name="pin" size={17} className="header__pin" />
        <select
          className="header__select ui"
          value={cityId ?? ''}
          onChange={(e) => onCity(e.target.value === '' ? null : Number(e.target.value))}
          aria-label={T.header.cityPlaceholder}
        >
          <option value="">{T.feed.allCities}</option>
          {cities.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <Icon name="chevron-down" size={14} className="header__chev" />
      </div>

      <span className="header__date caption muted tnum">{dayLabelKey(todayKey())}</span>

      <button
        type="button"
        className="header__theme"
        onClick={toggleTheme}
        aria-label={theme === 'dark' ? T.header.themeLight : T.header.themeDark}
        title={theme === 'dark' ? T.header.themeLight : T.header.themeDark}
      >
        <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={19} />
      </button>
    </header>
  );
}
