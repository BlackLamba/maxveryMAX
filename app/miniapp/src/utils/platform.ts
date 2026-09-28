/**
 * MAX Bridge (dev.max.ru/docs/webapps/bridge): обёртка над window.WebApp.
 *
 * Внутри MAX скрипт max-web-app.js (index.html) создаёт window.WebApp с
 * initDataUnsafe (user.id, start_param), openLink, BackButton, HapticFeedback.
 * В обычном браузере объекта нет — все функции деградируют безопасно,
 * поэтому мини-апп отлаживается вне мессенджера без единой заглушки данных.
 *
 * Темы у MAX Bridge нет (проверено по докам 2026-09) — тему берём из
 * prefers-color-scheme хоста + ручной переключатель (components/MaxUIProvider).
 */

interface InitDataUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
}

export interface MaxWebApp {
  initData?: string;
  initDataUnsafe?: {
    query_id?: string;
    auth_date?: number;
    hash?: string;
    user?: InitDataUser;
    chat?: { id: number; type: 'DIALOG' | 'CHAT' | 'CHANNEL' };
    start_param?: string;
  };
  platform?: 'ios' | 'android' | 'desktop' | 'web' | string;
  version?: string;
  deviceName?: string;
  openLink?: (url: string) => void;
  BackButton?: {
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
    isVisible?: boolean;
  };
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy', vibrationFallback?: boolean) => void;
  };
}

export function webApp(): MaxWebApp | undefined {
  if (typeof window === 'undefined') return undefined;
  return (window as unknown as { WebApp?: MaxWebApp }).WebApp;
}

export function isInsideMax(): boolean {
  return webApp() !== undefined;
}

export function platformInfo(): { platform: string; deviceName: string | null; version: string | null } {
  const wa = webApp();
  return {
    platform: wa?.platform ?? 'browser',
    deviceName: wa?.deviceName ?? null,
    version: wa?.version ?? null,
  };
}

const LS_DEV_USER = 'mxm.devUserId';

function stableDevId(): string {
  let id: string | null = null;
  try {
    id = localStorage.getItem(LS_DEV_USER);
  } catch {
    /* приватный режим — работаем без персистентности */
  }
  if (!id) {
    const rnd =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    id = `dev-${rnd}`;
    try {
      localStorage.setItem(LS_DEV_USER, id);
    } catch {
      /* не критично */
    }
  }
  return id;
}

/**
 * user_id для favorites/preferences/clicks:
 * внутри MAX — id пользователя из initDataUnsafe (строка),
 * в браузере — стабильный dev-id из localStorage, чтобы избранное работало
 * и при локальной отладке.
 */
export function getUserId(): string {
  const uid = webApp()?.initDataUnsafe?.user?.id;
  if (uid !== undefined && uid !== null) return String(uid);
  return stableDevId();
}

export function getUserName(): string | null {
  const u = webApp()?.initDataUnsafe?.user;
  if (!u) return null;
  return [u.first_name, u.last_name].filter(Boolean).join(' ') || u.username || null;
}

/** start_param deep link'а от бота (https://max.ru/<bot>?startapp=<payload>). */
export function getStartParam(): string | undefined {
  const raw = webApp()?.initDataUnsafe?.start_param;
  return raw && raw.length > 0 ? raw : undefined;
}

/**
 * Открытие внешней ссылки: в MAX — WebApp.openLink (внешний браузер),
 * в обычном браузере — window.open. Вызывать только из user-gesture
 * (Bridge сам проверяет клик — наше «Купить билет» и есть клик).
 */
export function openExternal(url: string): void {
  const wa = webApp();
  if (wa?.openLink) {
    try {
      wa.openLink(url);
      return;
    } catch {
      /* падаем на window.open */
    }
  }
  window.open(url, '_blank', 'noopener,noreferrer');
}

/** Тактильный отклик в MAX (на десктопе/в браузере — no-op). */
export function haptic(style: 'light' | 'medium' | 'heavy' = 'light'): void {
  try {
    webApp()?.HapticFeedback?.impactOccurred(style, true);
  } catch {
    /* игнорируем: haptic — не критичный путь */
  }
}

/**
 * Кнопка «Назад» в шапке MAX: показать на экране деталей, спрятать при уходе.
 * Возвращает функцию-очистку. В браузере — no-op (есть свой «‹ Назад»).
 */
export function withHostBackButton(onBack: () => void): () => void {
  const bb = webApp()?.BackButton;
  if (!bb) return () => undefined;
  try {
    bb.show();
    bb.onClick(onBack);
  } catch {
    return () => undefined;
  }
  return () => {
    try {
      bb.offClick(onBack);
      bb.hide();
    } catch {
      /* уже закрыто */
    }
  };
}
