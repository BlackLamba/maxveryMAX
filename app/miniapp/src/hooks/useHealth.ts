/**
 * Health-check при старте: GET /api/health.
 * 'down' — отдельный осмысленный экран «Сервис недоступен» (не спиннер),
 * 'degraded' (db: error) — баннер сверху, приложение продолжает работать.
 * Во время повторной проверки экран «недоступен» остаётся (checking=true),
 * чтобы не мелькать скелетонами ленты.
 */
import { useCallback, useEffect, useState } from 'react';
import { api } from '@/api/client';

export type HealthState = 'checking' | 'ok' | 'degraded' | 'down';

export function useHealth() {
  const [health, setHealth] = useState<HealthState>('checking');
  const [checking, setChecking] = useState(false);

  const check = useCallback(async () => {
    setChecking(true);
    try {
      const h = await api.health();
      setHealth(h.status === 'degraded' ? 'degraded' : 'ok');
    } catch {
      setHealth('down');
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  return { health, checking, recheck: check };
}
