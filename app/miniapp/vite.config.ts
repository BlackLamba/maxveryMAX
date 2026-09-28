import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const r = (p: string) => fileURLToPath(new URL(p, import.meta.url));

// Dev-прокси /api → backend (по умолчанию http://127.0.0.1:8000 — см. app/.env.example,
// BACKEND_PORT). В проде /api проксирует nginx (miniapp/nginx.conf), браузерный код
// всегда использует относительный путь (README 5.4: никаких захардкоженных localhost).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': r('./src'),
      // Общий справочник категорий живёт в app/shared (инвариант: не дублируем).
      '@shared': r('../shared'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: Number(process.env.MINIAPP_PORT ?? 3000),
    strictPort: true,
    // Мини-апп открывается во внешних preview-окружениях (MAX-клиент, песочницы).
    allowedHosts: true,
    fs: {
      // Разрешаем dev-серверу читать app/shared/ (лежит выше корня мини-аппа).
      allow: [r('..')],
    },
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
