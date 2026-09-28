/**
 * Инлайн-SVG иконки (без внешних библиотек). 24×24, currentColor,
 * stroke/fill по смыслу: закладка — «спрятать билет», афиша — билет с
 * перфорацией, фильтры — движки.
 */
import type { ReactElement, SVGProps } from 'react';

export type IconName =
  | 'bookmark'
  | 'bookmark-filled'
  | 'ticket'
  | 'chevron-down'
  | 'chevron-left'
  | 'close'
  | 'sliders'
  | 'refresh'
  | 'pin'
  | 'sun'
  | 'moon'
  | 'sort';

const PATHS: Record<IconName, ReactElement> = {
  bookmark: (
    <path
      d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-4-6 4V4.5Z"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
  ),
  'bookmark-filled': (
    <path d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-4-6 4V4.5Z" fill="currentColor" />
  ),
  ticket: (
    <>
      <path
        d="M3 8.5V6.8c0-.7.6-1.3 1.3-1.3h15.4c.7 0 1.3.6 1.3 1.3v1.7a2.6 2.6 0 0 0 0 5.2v3.5c0 .7-.6 1.3-1.3 1.3H4.3c-.7 0-1.3-.6-1.3-1.3v-3.5a2.6 2.6 0 0 0 0-5.2Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path d="M14 5.5v13" stroke="currentColor" strokeWidth="1.8" strokeDasharray="2 2.6" />
    </>
  ),
  'chevron-down': (
    <path
      d="m5.5 9 6.5 6.5L18.5 9"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  ),
  'chevron-left': (
    <path
      d="M14.5 5 8 11.5l6.5 6.5"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  ),
  close: (
    <path
      d="M6 6l12 12M18 6 6 18"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  ),
  sliders: (
    <>
      <path d="M4 7h10M18 7h2M4 17h4M12 17h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="16" cy="7" r="2.2" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="10" cy="17" r="2.2" fill="none" stroke="currentColor" strokeWidth="2" />
    </>
  ),
  sort: (
    <path
      d="M7 4v16m0 0-3.2-3.4M7 20l3.2-3.4M17 20V4m0 0-3.2 3.4M17 4l3.2 3.4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  ),
  refresh: (
    <path
      d="M20 12a8 8 0 1 1-2.6-5.9M20 4v4h-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  ),
  pin: (
    <>
      <path
        d="M12 21s7-5.3 7-11a7 7 0 1 0-14 0c0 5.7 7 11 7 11Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="10" r="2.6" fill="none" stroke="currentColor" strokeWidth="1.8" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M18.5 5.5l-1.7 1.7M7.2 16.8l-1.7 1.7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </>
  ),
  moon: (
    <path
      d="M20 14.2A8.4 8.4 0 0 1 9.8 4 8.5 8.5 0 1 0 20 14.2Z"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    />
  ),
};

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 24, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {PATHS[name]}
    </svg>
  );
}
