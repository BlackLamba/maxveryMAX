# 03. Роли, ответственность и порядок выполнения

## 1. Состав команды

Команда:

- Backend / Lead / Product Manager
- ML / Backend
- Frontend / Аналитика
- Frontend

## 2. Ответственность Backend / Lead / PM

Главный владелец архитектуры и интеграции.

### Ответственность
- архитектура;
- структура репозитория;
- PostgreSQL;
- Event Model;
- OpenAPI;
- MAX Bot;
- MAX integration;
- provider adapters;
- CI/CD и deployment;
- контроль scope.

### Главный результат

К концу первой технической итерации должен существовать рабочий backend skeleton с API-контрактом.

## 3. Ответственность ML / Backend

Главный фокус — intelligent search, а не «нейросеть ради нейросети».

### P0
- схема intent/entity extraction;
- structured query из естественного языка;
- базовый ranking;
- дедупликация событий.

### P1
- embeddings;
- semantic search;
- персонализация по действиям пользователя.

### Результат

```text
user query
   ↓
parser / ML
   ↓
structured query
   ↓
search + ranking
```

## 4. Ответственность Frontend / Аналитика

### Продуктовая часть
- пользовательские сценарии;
- customer journey;
- набор MVP-фич;
- KPI;
- события аналитики;
- UX-логика;
- acceptance criteria.

### Analytics events

Минимум:

```text
app_open
city_selected
interest_selected
search_started
natural_search
filter_used
event_opened
favorite_added
purchase_clicked
share_clicked
notification_enabled
```

## 5. Ответственность Frontend

### P0
- MAX Mini App skeleton;
- главный экран;
- карточки;
- поиск;
- фильтры;
- event detail;
- favorites;
- profile/settings.

### P1
- карта;
- polish;
- share;
- advanced states.

Frontend разрабатывается по OpenAPI и не зависит от деталей KudaGo/Timepad.

# 6. Порядок выполнения

## Шаг 1 — зафиксировать продукт

Решить за одну короткую встречу:
- основной пользователь;
- основная ценность;
- MVP;
- P1;
- что точно не делаем.

Главная формулировка:

> Пользователь говорит, чем хочет заняться, а MAX подбирает реальные подходящие мероприятия в выбранном городе и ведёт к покупке.

## Шаг 2 — API contract

Backend Lead описывает OpenAPI.

Frontend получает mock responses.

Это позволяет работать параллельно.

## Шаг 3 — Event Model + DB

Создать:
- events;
- sources;
- users;
- preferences;
- favorites.

## Шаг 4 — загрузка данных

Backend + Worker:

```text
KudaGo
Timepad
   ↓
adapters
   ↓
normalize
   ↓
validate
   ↓
deduplicate
   ↓
PostgreSQL
```

## Шаг 5 — базовый Mini App

Frontend:
- city;
- feed;
- filters;
- card;
- detail.

## Шаг 6 — NLP search

ML/Backend:
- parser;
- mapping;
- search endpoint;
- ranking.

## Шаг 7 — Bot

Backend:
- запуск;
- deeplink;
- notification;
- reminder.

## Шаг 8 — favorites + notifications

Интегрировать frontend с backend и Bot.

## Шаг 9 — полировка

Добавлять только то, что улучшает demo:
- карта;
- share;
- красивый empty state;
- fallback;
- loading;
- error handling.

## 7. Параллельные ветки Git

Рекомендуется:

```text
main

feature/backend-core
feature/event-ingestion
feature/ml-search
feature/frontend-feed
feature/frontend-event-page
feature/max-bot
feature/analytics
```

Каждая задача → отдельная feature-ветка → MR → review → merge.

## 8. Definition of Done для MVP

MVP считается готовым, если:

- пользователь открывает Mini App;
- выбирает город;
- видит реальные события;
- фильтрует их;
- открывает карточку;
- может сохранить событие;
- может перейти к покупке;
- может сделать естественно-языковой поиск;
- бот умеет отправить хотя бы одно полезное уведомление.
