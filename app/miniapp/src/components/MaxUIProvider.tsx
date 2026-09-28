/**
 * Провайдер контекста MAX-хоста: тема (light/dark), user_id, сведения о
 * платформе. Инициализируется в точке входа (main.tsx).
 *
 * Тема: MAX Bridge не отдаёт цветовую схему (проверено по докам Bridge,
 * 2026-09) → берём prefers-color-scheme хоста как сигнал системы + ручной
 * переключатель. Пока пользователь не переключил тему сам — следуем за
 * хостом; после переключения выбор запоминается (localStorage) и имеет
 * приоритет.
 *
 * user_id: initDataUnsafe.user.id внутри MAX; в браузере — стабильный dev-id
 * (utils/platform.ts), чтобы закладки/предпочтения работали при отладке.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { getUserId, getUserName, isInsideMax, platformInfo } from '@/utils/platform';

export type Theme = 'light' | 'dark';

const LS_THEME = 'mxm.theme';
const LS_THEME_MANUAL = 'mxm.themeManual';

interface MaxUIState {
  theme: Theme;
  toggleTheme: () => void;
  userId: string;
  userName: string | null;
  insideMax: boolean;
  platform: string;
  deviceName: string | null;
}

const MaxUICtx = createContext<MaxUIState | null>(null);

function lsGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function lsSet(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* приватный режим — работаем без персистентности */
  }
}

function systemTheme(): Theme {
  if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

function initialTheme(): Theme {
  // Ручной выбор важнее темы хоста.
  if (lsGet(LS_THEME_MANUAL) === '1') {
    const saved = lsGet(LS_THEME);
    if (saved === 'dark' || saved === 'light') return saved;
  }
  return systemTheme();
}

export function MaxUIProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  // Синхронизация темы с <html data-theme> и <meta theme-color>.
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#101A2E' : '#EDF0F5');
    lsSet(LS_THEME, theme);
  }, [theme]);

  // Пока тему не переключали вручную — следуем за хостом (системой).
  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!mq) return;
    const onChange = (e: MediaQueryListEvent) => {
      if (lsGet(LS_THEME_MANUAL) !== '1') setTheme(e.matches ? 'dark' : 'light');
    };
    mq.addEventListener?.('change', onChange);
    return () => mq.removeEventListener?.('change', onChange);
  }, []);

  const toggleTheme = useCallback(() => {
    lsSet(LS_THEME_MANUAL, '1');
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  }, []);

  const info = useMemo(() => platformInfo(), []);
  const userId = useMemo(() => getUserId(), []);
  const userName = useMemo(() => getUserName(), []);

  const value = useMemo<MaxUIState>(
    () => ({
      theme,
      toggleTheme,
      userId,
      userName,
      insideMax: isInsideMax(),
      platform: info.platform,
      deviceName: info.deviceName,
    }),
    [theme, toggleTheme, userId, userName, info],
  );

  return <MaxUICtx.Provider value={value}>{children}</MaxUICtx.Provider>;
}

export function useMaxUI(): MaxUIState {
  const ctx = useContext(MaxUICtx);
  if (!ctx) throw new Error('useMaxUI вне <MaxUIProvider>');
  return ctx;
}
