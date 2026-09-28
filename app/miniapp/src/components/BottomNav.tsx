/**
 * Нижняя навигация: Афиша / Закладки (со счётчиком). Safe-area снизу,
 * большой палец: высота 56px + inset. Активная вкладка — янтарная точка
 * (свет) + усиленный цвет; в тёмной теме активный текст янтарный (9.5:1),
 * в светлой — чернильный (Lamp на Paper не прошёл бы контраст для текста).
 */
import { NavLink } from 'react-router-dom';
import { useFavorites } from '@/hooks/useFavorites';
import { Icon } from '@/components/Icon';
import { T } from '@/utils/texts';

export function BottomNav() {
  const fav = useFavorites();

  return (
    <nav className="nav" aria-label="Разделы приложения">
      <NavLink
        to="/"
        end
        className={({ isActive }) => `nav__link${isActive ? ' nav__link--active' : ''}`}
      >
        <span className="nav__icon">
          <Icon name="ticket" size={22} />
        </span>
        <span className="nav__label caption">{T.nav.feed}</span>
      </NavLink>

      <NavLink
        to="/favorites"
        className={({ isActive }) => `nav__link${isActive ? ' nav__link--active' : ''}`}
      >
        <span className="nav__icon">
          <Icon name="bookmark" size={22} />
          {fav.count > 0 && (
            <span className="nav__count caption tnum" aria-label={`${fav.count}`}>
              {fav.count}
            </span>
          )}
        </span>
        <span className="nav__label caption">{T.nav.favorites}</span>
      </NavLink>
    </nav>
  );
}
