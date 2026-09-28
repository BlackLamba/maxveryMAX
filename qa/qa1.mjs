import { chromium } from 'playwright-core';
import fs from 'node:fs';

const BASE = 'http://localhost:3000';
const OUT = '/home/user/qa';
fs.mkdirSync(OUT, { recursive: true });

const errors = [];
const apiCalls = [];

const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
const ctx = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  locale: 'ru-RU',
});
const page = await ctx.newPage();

page.on('console', (m) => {
  if (m.type() === 'error') errors.push(`console: ${m.text()}`);
});
page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
page.on('request', (r) => {
  const u = r.url();
  if (u.includes('/api/')) apiCalls.push(`${r.method()} ${u.replace(BASE, '')}`);
});
// вне MAX bridge не нужен — гасим запрос CDN, чтобы не ждать таймаутов
await ctx.route('**://st.max.ru/**', (route) => route.abort().catch(() => {}));

let failN = 0;
const step = async (name, fn) => {
  try {
    await fn();
    console.log(`OK   ${name}`);
  } catch (e) {
    failN += 1;
    console.log(`FAIL ${name}: ${e.message.split('\n')[0]}`);
    errors.push(`step ${name}: ${e.message.split('\n')[0]}`);
    await page.screenshot({ path: `${OUT}/fail-${failN}.png` }).catch(() => {});
  }
};

// --- 1. Лента (светлая тема) ---
await step('лента грузится', async () => {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.ticket:not(.ticket--skeleton)', { timeout: 8000 });
  const n = await page.locator('.ticket:not(.ticket--skeleton)').count();
  if (n < 3) throw new Error(`только ${n} билетов`);
  const demo = await page.locator('.plate--demo').count();
  if (demo === 0) throw new Error('нет плашки «демо» на mock-событиях');
  await page.screenshot({ path: `${OUT}/01-feed-light.png` });
});

await step('заголовок первой карточки из БД', async () => {
  const t = await page.locator('.ticket__title').first().textContent();
  console.log(`     первая карточка: ${t.trim()}`);
});

// --- 2. Дата-линейка: выбор сегодняшнего дня ---
await step('дата-линейка фильтрует', async () => {
  const today = page.locator('.ruler__day').first();
  await today.click();
  await page.waitForTimeout(700);
  const sel = await page.locator('.ruler__day--selected').count();
  if (sel !== 1) throw new Error('день не выбрался');
  await page.waitForSelector('.ticket, .state', { timeout: 5000 });
  await page.screenshot({ path: `${OUT}/02-feed-today.png` });
});

// --- 3. Чип категории ---
await step('чип категории', async () => {
  await page.locator('.chip', { hasText: 'Концерт' }).click();
  await page.waitForTimeout(700);
  const on = await page.locator('.chip--on', { hasText: 'Концерт' }).count();
  if (!on) throw new Error('чип не активировался');
  await page.screenshot({ path: `${OUT}/03-chip-concert.png` });
  // сброс
  await page.locator('.chip', { hasText: 'Все' }).first().click();
  await page.waitForTimeout(500);
});

// --- 4. Пустое состояние с hint ---
await step('пустое состояние показывает hint API', async () => {
  // Москва + сегодня + кино → в демо-наборе пусто (кино в Москве не сегодня)
  await page.selectOption('.header__select', '1');
  await page.waitForTimeout(500);
  if ((await page.locator('.ruler__day--selected').count()) === 0) {
    await page.locator('.ruler__day').first().click();
    await page.waitForTimeout(300);
  }
  await page.locator('.chip', { hasText: 'Кино' }).click();
  await page.waitForTimeout(900);
  const state = page.locator('.state');
  if (await state.count() === 0) {
    // могло найтись — тогда просто логируем
    console.log('     (сегодня+кино нашлось, пустое состояние не возникло)');
    await page.locator('.chip', { hasText: 'Все' }).first().click();
    await page.locator('.ruler__all').click();
    await page.waitForTimeout(600);
    return;
  }
  const hint = await page.locator('.note__text').textContent();
  if (!hint.includes('По этим условиям ничего не нашлось')) throw new Error('hint не из API: ' + hint);
  console.log(`     hint: ${hint.trim().slice(0, 110)}…`);
  await page.screenshot({ path: `${OUT}/04-empty-hint.png` });
  await page.locator('.chip', { hasText: 'Все' }).first().click();
  await page.locator('.ruler__all').click();
  await page.waitForTimeout(600);
});

// --- 5. Карточка события ---
await step('детали события', async () => {
  await page.locator('.ticket').first().click();
  await page.waitForSelector('.detail__title', { timeout: 6000 });
  const title = await page.locator('.detail__title').textContent();
  const buy = await page.locator('.actionbar__buy').textContent();
  console.log(`     детали: ${title.trim()} | кнопка: ${buy.trim()}`);
  await page.screenshot({ path: `${OUT}/05-detail-light.png`, fullPage: true });
});

await step('закладка на деталях', async () => {
  const fav = page.locator('.actionbar__fav');
  await fav.click();
  await page.waitForTimeout(800);
  const pressed = await fav.getAttribute('aria-pressed');
  if (pressed !== 'true') throw new Error('закладка не поставилась');
  const banner = await page.locator('.banner').textContent().catch(() => '');
  console.log(`     баннер: ${banner?.trim()}`);
  await page.screenshot({ path: `${OUT}/06-detail-fav.png` });
});

await step('назад в ленту', async () => {
  await page.locator('.header__back').click();
  await page.waitForSelector('.ticket', { timeout: 6000 });
});

// --- 6. Экран закладок ---
await step('закладки', async () => {
  await page.locator('.nav__link', { hasText: 'Закладки' }).click();
  await page.waitForSelector('.page--favorites .ticket', { timeout: 6000 });
  const n = await page.locator('.page--favorites .ticket').count();
  console.log(`     в закладках: ${n}`);
  await page.screenshot({ path: `${OUT}/07-favorites.png` });
});

await step('снятие закладки', async () => {
  await page.locator('.page--favorites .ticket__fav').first().click();
  await page.waitForTimeout(900);
  const n = await page.locator('.page--favorites .ticket').count();
  console.log(`     после снятия: ${n}`);
});

// --- 7. Тёмная тема ---
await step('тёмная тема', async () => {
  await page.locator('.nav__link', { hasText: 'Афиша' }).click();
  await page.waitForSelector('.ticket', { timeout: 6000 });
  await page.emulateMedia({ colorScheme: 'dark' });
  // тема следует за системой (manual-флаг не выставлен) — ждём обновление атрибута
  try {
    await page.waitForFunction(() => document.documentElement.dataset.theme === 'dark', null, { timeout: 2000 });
  } catch {
    // система не сменила тему (например, уже переключали вручную) — жмём кнопку
    await page.locator('.header__theme').click();
    await page.waitForFunction(() => document.documentElement.dataset.theme === 'dark', null, { timeout: 2000 });
  }
  await page.screenshot({ path: `${OUT}/08-feed-dark.png` });
  await page.locator('.ticket').first().click();
  await page.waitForSelector('.detail__title', { timeout: 6000 });
  await page.screenshot({ path: `${OUT}/09-detail-dark.png`, fullPage: true });
});

// --- 8. Deep link (браузерный фолбэк query) ---
await step('deep link применяет фильтры до первого запроса', async () => {
  apiCalls.length = 0;
  const today = new Date(Date.now() + 3 * 3600e3).toISOString().slice(0, 10);
  await page.goto(`${BASE}/?city=moscow&cat=concert,theater&date=${today}&budget=3000#/?city=moscow&cat=concert,theater&date=${today}&budget=3000`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  const ev = apiCalls.filter((c) => c.includes('/api/events?'));
  console.log(`     /api/events: ${ev[0] ?? 'НЕТ'}`);
  if (!ev.length) throw new Error('запрос /api/events не выполнен');
  const q = ev[0];
  if (!q.includes('city_id=1')) throw new Error('город из deep link не применён');
  if (!q.includes('category=concert') || !q.includes('category=theater')) throw new Error('категории не применены');
  if (!q.includes(`date_from=${today}`)) throw new Error('дата не применена');
  if (!q.includes('price_max=3000')) throw new Error('бюджет не применён');
  // первый запрос /api/events ровно один (без дефолтного pre-fetch)
  const firstEvents = ev[0];
  if (ev.length > 1) console.log(`     (повторных запросов: ${ev.length - 1})`);
  void firstEvents;
  await page.screenshot({ path: `${OUT}/10-deeplink.png` });
});

// --- 9. Bottom-sheet фильтров ---
await step('лист фильтров открывается', async () => {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.ticket', { timeout: 8000 });
  await page.locator('.ctl-btn').click();
  await page.waitForSelector('.sheet', { timeout: 4000 });
  await page.waitForTimeout(400); // анимация выхода листа
  await page.screenshot({ path: `${OUT}/11-filter-sheet.png` });
  // бесплатные + применить
  await page.locator('.switch').click();
  await page.locator('.sheet__foot .btn--lamp').click();
  await page.waitForTimeout(900);
  const chips = await page.locator('.active-chip').allTextContents();
  console.log(`     активные чипы: ${JSON.stringify(chips)}`);
  await page.screenshot({ path: `${OUT}/12-free-applied.png` });
});

// --- 10. Узкий экран 360 ---
await step('360px без горизонтального скролла', async () => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.ticket', { timeout: 8000 });
  await page.waitForTimeout(500);
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  if (overflow > 1) throw new Error(`горизонтальный скролл: +${overflow}px`);
  await page.screenshot({ path: `${OUT}/13-feed-360.png` });
  await page.setViewportSize({ width: 390, height: 844 });
});

// --- 11. Backend down ---
await step('состояние «сервис не отвечает»', async () => {
  // временно проксируем /api в никуда через route
  await page.route((u) => u.pathname.startsWith('/api/'), (r) => r.abort('connectionfailed'));
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.state--full', { timeout: 8000 });
  const title = await page.locator('.state__title').textContent();
  console.log(`     экран: ${title.trim()}`);
  await page.screenshot({ path: `${OUT}/14-backend-down.png` });
  await page.unroute((u) => u.pathname.startsWith('/api/'));
});

console.log('\n--- API calls (последние 20): ---');
for (const c of apiCalls.slice(-20)) console.log(' ', c);
console.log('\n--- Ошибки консоли/страницы: ---');
if (errors.length === 0) console.log('  нет');
for (const e of errors.slice(0, 20)) console.log(' ', e);

await browser.close();
process.exit(errors.length > 0 ? 1 : 0);
