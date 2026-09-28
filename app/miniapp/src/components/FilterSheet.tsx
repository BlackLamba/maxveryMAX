/**
 * Фильтры — bottom-sheet («печатный лист» поверх ленты): бюджет, только
 * бесплатные, окно времени (валидно лишь для одного дня — контракт
 * EventFilters), «рядом со мной» (геолокация + радиус).
 *
 * Правки живут в черновике и применяются кнопкой «Показать события» —
 * один тап = один запрос. «Сохранить для следующих подборок» —
 * POST /api/preferences (categories + price_max + radius_km).
 */
import { useCallback, useEffect, useState } from 'react';
import type { ActiveFilters } from '@/hooks/useFilters';
import { api } from '@/api/client';
import { useBanner } from '@/components/BannerHost';
import { useMaxUI } from '@/components/MaxUIProvider';
import { formatRub } from '@/utils/format';
import type { CategorySlug } from '@shared/categories';
import { Icon } from '@/components/Icon';
import { T } from '@/utils/texts';

const BUDGET_MAX = 5000;
const BUDGET_STEP = 250;
const RADIUS_MAX = 50;

interface Draft {
  isFree: boolean;
  priceMax: number | null;
  timeFrom: string | null;
  timeTo: string | null;
  lat: number | null;
  lon: number | null;
  radiusKm: number | null;
}

interface Props {
  open: boolean;
  filters: ActiveFilters;
  onClose: () => void;
  onApply: (d: {
    isFree: boolean;
    priceMax: number | null;
    timeFrom: string | null;
    timeTo: string | null;
    lat: number | null;
    lon: number | null;
    radiusKm: number | null;
  }) => void;
}

function toDraft(f: ActiveFilters): Draft {
  return {
    isFree: f.isFree,
    priceMax: f.priceMax,
    timeFrom: f.timeFrom,
    timeTo: f.timeTo,
    lat: f.lat,
    lon: f.lon,
    radiusKm: f.radiusKm,
  };
}

export function FilterSheet({ open, filters, onClose, onApply }: Props) {
  const banner = useBanner();
  const { userId } = useMaxUI();
  const [draft, setDraft] = useState<Draft>(() => toDraft(filters));
  const [geoBusy, setGeoBusy] = useState(false);
  const [geoError, setGeoError] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);

  // открытие — синхронизируем черновик с текущими фильтрами
  useEffect(() => {
    if (open) {
      setDraft(toDraft(filters));
      setGeoError(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // Esc закрывает лист (клавиатура)
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const singleDay = filters.dateFrom !== null && filters.dateFrom === filters.dateTo;

  const locate = useCallback(() => {
    if (!navigator.geolocation) {
      setGeoError(true);
      return;
    }
    setGeoBusy(true);
    setGeoError(false);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoBusy(false);
        setDraft((d) => ({
          ...d,
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          radiusKm: d.radiusKm ?? 5,
        }));
      },
      () => {
        setGeoBusy(false);
        setGeoError(true);
      },
      { timeout: 8000, maximumAge: 300_000 },
    );
  }, []);

  const dropGeo = useCallback(() => {
    setDraft((d) => ({ ...d, lat: null, lon: null, radiusKm: null }));
  }, []);

  const savePrefs = useCallback(async () => {
    setSavingPrefs(true);
    try {
      await api.savePreferences({
        user_id: userId,
        categories: filters.categories as CategorySlug[],
        price_max: draft.priceMax,
        radius_km: draft.lat !== null ? draft.radiusKm : null,
      });
      banner.show(T.filters.prefsSaved, 'ok');
    } catch {
      banner.show(T.filters.prefsFailed, 'error');
    } finally {
      setSavingPrefs(false);
    }
  }, [userId, filters.categories, draft.priceMax, draft.radiusKm, draft.lat, banner]);

  if (!open) return null;

  return (
    <div className="sheet-backdrop" onClick={onClose} role="presentation">
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-label={T.filters.title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sheet__grab" aria-hidden="true" />
        <div className="sheet__head">
          <h2 className="sheet__title t-section">{T.filters.title}</h2>
          <button type="button" className="sheet__close" onClick={onClose} aria-label={T.filters.close}>
            <Icon name="close" size={18} />
          </button>
        </div>

        <div className="sheet__body">
          {/* Только бесплатные */}
          <label className="field field--row">
            <span className="field__label ui">{T.filters.freeOnly}</span>
            <button
              type="button"
              role="switch"
              className={`switch${draft.isFree ? ' switch--on' : ''}`}
              aria-checked={draft.isFree}
              onClick={() => setDraft((d) => ({ ...d, isFree: !d.isFree }))}
            >
              <span className="switch__knob" />
            </button>
          </label>

          {/* Бюджет */}
          <div className="field">
            <div className="field__row">
              <span className="field__label ui">{T.filters.budget}</span>
              <span className="field__value ui tnum">
                {draft.priceMax === null ? T.filters.anyBudget : formatRub(draft.priceMax)}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={BUDGET_MAX}
              step={BUDGET_STEP}
              value={draft.priceMax ?? BUDGET_MAX}
              disabled={draft.priceMax === null}
              onChange={(e) => setDraft((d) => ({ ...d, priceMax: Number(e.target.value) }))}
              aria-label={T.filters.budget}
            />
            <button
              type="button"
              className="link-btn caption"
              onClick={() =>
                setDraft((d) => ({ ...d, priceMax: d.priceMax === null ? 1500 : null }))
              }
            >
              {draft.priceMax === null ? 'Ограничить бюджет' : T.filters.anyBudget}
            </button>
          </div>

          {/* Окно времени — только для одного дня (контракт EventFilters) */}
          <div className={`field${singleDay ? '' : ' field--disabled'}`}>
            <div className="field__row">
              <span className="field__label ui">{T.filters.timeWindow}</span>
            </div>
            <div className="field__times">
              <label className="time-input">
                <span className="caption">{T.filters.timeFrom}</span>
                <input
                  type="time"
                  value={draft.timeFrom ?? ''}
                  disabled={!singleDay}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, timeFrom: e.target.value || null }))
                  }
                />
              </label>
              <label className="time-input">
                <span className="caption">{T.filters.timeTo}</span>
                <input
                  type="time"
                  value={draft.timeTo ?? ''}
                  disabled={!singleDay}
                  onChange={(e) => setDraft((d) => ({ ...d, timeTo: e.target.value || null }))}
                />
              </label>
            </div>
            {!singleDay && <p className="field__note caption">{T.filters.timeNeedsDay}</p>}
          </div>

          {/* Рядом со мной */}
          <div className="field">
            <div className="field__row">
              <span className="field__label ui">{T.filters.nearTitle}</span>
              {draft.lat !== null && (
                <button type="button" className="link-btn caption" onClick={dropGeo}>
                  {T.filters.radiusAny}
                </button>
              )}
            </div>
            {draft.lat === null ? (
              <button type="button" className="btn btn--ghost" onClick={locate} disabled={geoBusy}>
                <Icon name="pin" size={17} />
                {geoBusy ? T.filters.locating : T.filters.locate}
              </button>
            ) : (
              <>
                <div className="field__row">
                  <span className="field__label caption">{T.filters.radius}</span>
                  <span className="field__value ui tnum">
                    {draft.radiusKm === null ? T.filters.radiusAny : `${draft.radiusKm} км`}
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={RADIUS_MAX}
                  step={1}
                  value={draft.radiusKm ?? RADIUS_MAX}
                  disabled={draft.radiusKm === null}
                  onChange={(e) => setDraft((d) => ({ ...d, radiusKm: Number(e.target.value) }))}
                  aria-label={T.filters.radius}
                />
              </>
            )}
            {geoError && <p className="field__note field__note--warn caption">{T.filters.locateDenied}</p>}
          </div>
        </div>

        <div className="sheet__foot">
          {/* Сброс — только черновик; применится кнопкой «Показать события» */}
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() =>
              setDraft({
                isFree: false,
                priceMax: null,
                timeFrom: null,
                timeTo: null,
                lat: draft.lat,
                lon: draft.lon,
                radiusKm: null,
              })
            }
          >
            {T.filters.reset}
          </button>
          <button type="button" className="btn btn--lamp" onClick={() => onApply(draft)}>
            {T.filters.apply}
          </button>
        </div>

        <button
          type="button"
          className="sheet__save link-btn caption"
          onClick={() => void savePrefs()}
          disabled={savingPrefs}
        >
          {savingPrefs ? 'Сохраняем…' : T.filters.savePrefs}
        </button>
      </div>
    </div>
  );
}
