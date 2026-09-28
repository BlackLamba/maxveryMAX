/**
 * Баннер о результате действия (ResultBanner из README 5.4): короткая полоса
 * над нижней навигацией — «Добавлено в закладки», «Не удалось сохранить…».
 * Авто-скрывается; при prefers-reduced-motion появляется без движения.
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


export type BannerTone = 'ok' | 'error';

interface BannerState {
  show: (text: string, tone?: BannerTone) => void;
}

const BannerCtx = createContext<BannerState | null>(null);

const HIDE_MS = 2600;

export function BannerProvider({ children }: { children: ReactNode }) {
  const [banner, setBanner] = useState<{ text: string; tone: BannerTone; id: number } | null>(null);
  const timer = useRef<number | null>(null);
  const idRef = useRef(0);

  const show = useCallback((text: string, tone: BannerTone = 'ok') => {
    idRef.current += 1;
    setBanner({ text, tone, id: idRef.current });
  }, []);

  useEffect(() => {
    if (!banner) return;
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setBanner(null), HIDE_MS);
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [banner]);

  const value = useMemo<BannerState>(() => ({ show }), [show]);

  return (
    <BannerCtx.Provider value={value}>
      {children}
      <div className="banner-host" aria-live="polite" aria-atomic="true">
        {banner && (
          <div key={banner.id} className={`banner banner--${banner.tone}`} role="status">
            <span className="banner__dot" aria-hidden="true" />
            {banner.text}
          </div>
        )}
      </div>
    </BannerCtx.Provider>
  );
}

export function useBanner(): BannerState {
  const ctx = useContext(BannerCtx);
  if (!ctx) throw new Error('useBanner вне <BannerProvider>');
  return ctx;
}
