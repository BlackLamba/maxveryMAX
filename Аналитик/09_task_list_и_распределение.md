распределение модулей:
  1. чат-бот - Антон
  2. БЭК - Женя
  3. ФРОНТ - ДИМА
  4. ВОРКЕР - олежа.

Примерный ТУДУ лист на первое время:
этот ужас был накидан за 5 минут, ребята, не стесняйтесь менять, просто на всякий случай помечайте в этом файле и антону что вы изменили, особенно если в поле ответственности другого.

Общее:
Создать репозиторий и структуру папок: bot/, backend/, worker/, miniapp/, shared/, infra/ - пример
docker-compose.yml skeleton: postgres + backend + worker + bot + miniapp - пример
.env.example без токенов
shared/models.py — Pydantic-модель Event, City, Category - пример
shared/categories.py и shared/categories.ts — единый enum категорий
Схема БД: миграции для cities, categories, events, event_sources, tags, event_tags, providers, users, favorites, user_preferences - пример
Зафиксировать OpenAPI-контракт (можно markdown-таблицей на первом этапе)
Формат deep link: https://miniapp.example/?city=...&date=...&category=...&price_max=...
Формат передачи параметров бот → мини-апп
Общее правило: воркер пишет в БД, бэк читает из БД, бот и мини-апп ходят только в бэк

Воркер:
worker/data/mock_events.json — 30–50 событий с полями из модели Event
worker/providers/base.py — интерфейс EventProvider
worker/providers/mock.py — читает JSON
worker/pipeline/normalize.py — raw → Event
worker/pipeline/validate.py — проверка обязательных полей
worker/repository.py — upsert в events, event_sources, tags, event_tags, providers
CLI-команда: python -m worker import --file data/mock_events.json
Проверка: после запуска в БД появились события
worker/pipeline/deduplicate.py — RapidFuzz по title + дата + адрес
quality_score — простая формула, записывается в events
worker/scheduler.py — периодический запуск (interval)
Обработка ошибок провайдера (retry, логирование)
seed.py — наполнение БД для бэка одной командой
Юнит-тесты на нормализацию и дедупликацию

Бэк:
FastAPI-скелет + подключение к PostgreSQL
GET /api/health
GET /api/cities
GET /api/categories
GET /api/events с фильтрами: city_id, date_from, date_to, price_max, category
GET /api/events/{id}
POST /api/search — упрощённый, принимает те же фильтры
Простое ранжирование: совпадение категории + времени + цены + свежесть
Поле reason в ответе — «почему подходит»
Уточнение фильтров: временное окно, радиус (если есть координаты)
Сортировки: по расстоянию, по цене, по релевантности
POST /api/search/natural — простой парсер фразы в фильтры
POST /api/favorites + GET /api/favorites + DELETE /api/favorites/{event_id}
POST /api/preferences + GET /api/preferences
Объяснение «почему подходит» — отдельным текстом в ответе
Обработка пустого результата: возвращать [] + подсказку смягчить фильтры
Корректные HTTP-коды и формат ошибок

Ботик:
Регистрация бота в MAX, токен в .env
/start — приветствие + объяснение назначения
Шаг «когда?»: кнопки «сегодня вечером», «завтра», «выходные»
Шаг «что?»: кнопки категорий (из shared/categories)
Шаг «бюджет?»: «бесплатно», «до 1000 ₽», «до 3000 ₽», «не важно»
Шаг «расстояние?»: «рядом», «в пределах города», «не важно»
Хранение состояния диалога (in-memory или Redis)
Кнопка «Показать варианты» → deep link в мини-апп с параметрами
Обработка повторного /start (сброс состояния)
Валидация ответов (непонятный ввод)
Возможность вернуться на шаг назад
Сброс диалога командой /reset
/help с краткой инструкцией
(опционально) Уведомления о новых событиях
(опционально) Напоминания о сохранённых событиях

Фронт:
Vite + React + TypeScript + MAX UI
HashRouter (для WebView)
API-клиент к бэкенду
Парсинг параметров из URL
Экран списка карточек
Компонент EventCard (название, время, цена, место, «почему подходит»)
Экран карточки события
Кнопка «Перейти к источнику» → внешняя ссылка
Локальный запуск через Vite dev server
Фильтры в мини-аппе без возврата в бот
Сортировки
Избранное: добавление/удаление, экран «Избранное»
Обязательные состояния: Loader, EmptyState, ErrorState
Скелетоны карточек
Баннер о результате действия
Адаптив: 360 / 375 / 390 / 414 / 430 px
Проверка на реальном iPhone и Android
Проверка в веб-версии MAX
Интеграция MAX Bridge (определение платформы)
