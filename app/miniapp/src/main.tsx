/**
 * Точка входа (README 5.4): провайдер MAX WebApp SDK (<MaxUI>) + HashRouter.
 * HashRouter — чтобы отдача статики nginx'ом не требовала rewrite'ов под
 * каждый маршрут (SPA-fallback есть, но hash надёжнее внутри WebView).
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import App from './App';

import './styles/fonts.css';
import './styles/tokens.css';
import './styles/global.css';
import './styles/app.css';

const rootEl = document.getElementById('root');
if (!rootEl) throw new Error('нет #root — проверьте index.html');

createRoot(rootEl).render(
  <StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </StrictMode>,
);
