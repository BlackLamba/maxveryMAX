/**
 * Обязательные состояния (README 5.4 + задача п.5.5) — каждое осмысленное
 * и отдельное:
 * - Skeletons: загрузка ленты в форме билетов (плоская пульсация, без
 *   shimmer-градиентов; reduced-motion — статичные);
 * - EmptyState: hint из конверта API дословно (backend уже сформулировал,
 *   что смягчить) + сброс фильтров;
 * - ErrorState: ошибка сети/сервера с «Повторить»;
 * - BackendDownState: /api/health не отвечает — отдельный экран, не спиннер.
 */
import type { ReactNode } from 'react';
import { ApiError } from '@/api/client';
import { Icon } from '@/components/Icon';
import { T } from '@/utils/texts';

/* --- Скелетоны --- */

export function TicketSkeleton() {
  return (
    <div className="ticket ticket--skeleton" aria-hidden="true">
      <div className="ticket__stub">
        <span className="sk sk--day" />
        <span className="sk sk--month" />
        <span className="sk sk--time" />
      </div>
      <div className="ticket__body">
        <span className="sk sk--title" />
        <span className="sk sk--title sk--short" />
        <span className="sk sk--line" />
        <div className="ticket__plates">
          <span className="sk sk--plate" />
          <span className="sk sk--plate sk--plate-sm" />
        </div>
      </div>
    </div>
  );
}

export function ListSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="list" role="status" aria-label="Загрузка афиши">
      {Array.from({ length: count }, (_, i) => (
        <TicketSkeleton key={i} />
      ))}
    </div>
  );
}

export function DetailSkeleton() {
  return (
    <div className="detail-skeleton" role="status" aria-label="Загрузка карточки">
      <span className="sk sk--chip" />
      <span className="sk sk--title sk--xl" />
      <span className="sk sk--title" />
      <span className="sk sk--plate-block" />
      <span className="sk sk--line" />
      <span className="sk sk--line" />
      <span className="sk sk--line sk--short" />
      <span className="sk sk--note" />
    </div>
  );
}

/* --- Пустое состояние: hint из API как есть --- */

export function EmptyState({
  hint,
  onReset,
  showReset = true,
}: {
  hint: string | null;
  onReset?: () => void;
  showReset?: boolean;
}) {
  return (
    <div className="state">
      <h2 className="state__title t-hero">{T.empty.title}</h2>
      <div className="note">
        {/* hint бэкенда показываем дословно — свой текст поверх не пишем */}
        <p className="note__text body">{hint ?? T.empty.fallbackBody}</p>
      </div>
      {showReset && onReset && (
        <button type="button" className="btn btn--ghost state__action" onClick={onReset}>
          {T.filters.clearAll}
        </button>
      )}
    </div>
  );
}

/* --- Ошибка сети / сервера --- */

export function ErrorState({
  error,
  onRetry,
  title,
}: {
  error?: ApiError | null;
  onRetry: () => void;
  title?: string;
}) {
  const isNetwork = !error || error.networkError || error.code === 'network_error';
  return (
    <div className="state">
      <h2 className="state__title t-hero">{title ?? T.error.title}</h2>
      <p className="state__body body">{isNetwork ? T.error.networkBody : T.error.serverBody}</p>
      {!isNetwork && error?.message && (
        <p className="state__detail caption muted">{error.message}</p>
      )}
      <button type="button" className="btn btn--lamp state__action" onClick={onRetry}>
        <Icon name="refresh" size={17} />
        {T.error.retry}
      </button>
    </div>
  );
}

/* --- Backend недоступен (health) --- */

export function BackendDownState({
  onRetry,
  checking,
}: {
  onRetry: () => void;
  checking: boolean;
}) {
  return (
    <div className="state state--full">
      <div className="state__lamp" aria-hidden="true" />
      <h2 className="state__title t-hero">{T.backendDown.title}</h2>
      <p className="state__body body">{T.backendDown.body}</p>
      <button
        type="button"
        className="btn btn--lamp state__action"
        onClick={onRetry}
        disabled={checking}
      >
        <Icon name="refresh" size={17} />
        {checking ? T.backendDown.checking : T.backendDown.retry}
      </button>
    </div>
  );
}

/* --- «Найдено не всё»: заглушка не найдена (404 деталей) --- */

export function NotFoundState({ action }: { action?: ReactNode }) {
  return (
    <div className="state">
      <h2 className="state__title t-hero">{T.details.notFoundTitle}</h2>
      <p className="state__body body">{T.details.notFoundBody}</p>
      {action}
    </div>
  );
}
