# 01. Архитектура

## 1. Архитектурное решение

Для хакатона рекомендуется **модульный монолит + worker**, а не набор микросервисов.

Причины:
- быстрее разработка и отладка;
- меньше DevOps-сложности;
- меньше Docker-контейнеров;
- удобно разделять работу по модулям;
- при этом границы модулей можно сохранить так, чтобы позже выделить отдельные сервисы.

Основная связка продукта:

```text
MAX Bot
   │
   ├── запуск / deeplink
   ├── уведомления
   └── напоминания
          │
          ▼
     MAX Mini App
          │
          ▼
   Backend API (Modular Monolith)
          │
   ┌──────┼───────────────┐
   │      │               │
   ▼      ▼               ▼
Events  Search      Recommendations
   │      │               │
   └──────┼───────────────┘
          │
      PostgreSQL
          │
      Event Catalog
          ▲
          │
      Background Worker
          │
    ┌─────┴─────┐
    ▼           ▼
 KudaGo      Timepad
```

## 2. Компоненты

### MAX Bot

Назначение:
- entry point в продукт;
- deeplink на конкретное событие или подборку;
- уведомления;
- напоминания о сохранённых событиях;
- уведомления о новых подходящих событиях.

Бот не должен быть основным интерфейсом каталога.

### MAX Mini App

Основной пользовательский UI:
- лента мероприятий;
- поиск;
- естественно-языковой запрос;
- фильтры;
- выбор города;
- карточка события;
- избранное;
- персональные рекомендации;
- карта как дополнительный режим;
- переход к покупке.

### Backend API

Единая точка доступа frontend к данным и бизнес-логике.

Рекомендуемые модули:

```text
backend/
├── users/
├── cities/
├── events/
├── providers/
│   ├── kudago/
│   └── timepad/
├── search/
├── recommendations/
├── favorites/
├── notifications/
├── analytics/
└── shared/
```

Каждый модуль имеет публичный интерфейс и внутреннюю реализацию.

## 3. Интеграция внешних API

Внешние источники не должны вызываться напрямую из frontend.

Правильный поток:

```text
KudaGo / Timepad
       ↓
Provider Adapter
       ↓
Normalization
       ↓
Validation
       ↓
Deduplication
       ↓
PostgreSQL
       ↓
Backend API
       ↓
Mini App
```

Такой подход позволяет:
- использовать несколько источников;
- скрыть различия API поставщиков;
- переживать временный отказ внешнего API;
- кэшировать события;
- не привязывать frontend к конкретному поставщику.

## 4. Единая модель Event

Рекомендуемая сущность:

```json
{
  "id": "internal-id",
  "source": "timepad",
  "source_id": "12345",
  "title": "Название мероприятия",
  "description": "Описание",
  "category": "concert",
  "tags": ["rock", "music"],
  "city": "Москва",
  "address": "...",
  "latitude": 55.75,
  "longitude": 37.61,
  "start_at": "2026-09-20T20:00:00",
  "end_at": null,
  "price_min": 2500,
  "price_max": 5000,
  "is_free": false,
  "image_url": "...",
  "source_url": "...",
  "purchase_url": "...",
  "quality_score": 0.91,
  "updated_at": "2026-09-15T10:00:00"
}
```

## 5. Дедупликация

Одно и то же мероприятие может прийти из нескольких источников.

MVP: детерминированный/эвристический score:

```text
match_score =
    0.40 * title_similarity +
    0.25 * organizer_similarity +
    0.20 * location_similarity +
    0.15 * date_similarity
```

При высоком score события объединяются в одну внутреннюю запись с несколькими источниками.

Для строкового similarity достаточно начать с нормализации + RapidFuzz. ML здесь не обязателен.

## 6. Поиск и рекомендации

Рекомендуемая последовательность зрелости:

### Уровень 1 — фильтры + ranking

```text
score =
  category_match
  + date_match
  + price_match
  + location_match
  + user_interest_match
  + freshness
```

### Уровень 2 — Natural Language Search

```text
"рок-концерт в Москве в субботу до 3000"
                  ↓
        structured query
                  ↓
 city=Moscow
 category=concert
 genre=rock
 date=Saturday
 price_max=3000
                  ↓
              search
```

### Уровень 3 — semantic search

Embedding запроса сравнивается с embedding текста мероприятия.

### Уровень 4 — Learning-to-Rank

Добавляется после накопления взаимодействий пользователей.

## 7. База данных

Для MVP достаточно PostgreSQL.

Основные таблицы:

```text
users
user_preferences
cities

events
event_sources
event_categories
event_tags

favorites
search_history
event_interactions

notification_subscriptions
notifications
```

Опционально:

```text
event_embeddings
```

## 8. Worker

Отдельный background worker выполняет:
- синхронизацию KudaGo;
- синхронизацию Timepad;
- нормализацию;
- дедупликацию;
- обновление quality score;
- подготовку embedding;
- планирование уведомлений.

Frontend никогда не должен ждать загрузки каталога от внешнего API.

## 9. Контракт API

Frontend и backend разрабатываются по OpenAPI.

Минимальный набор:

```http
GET  /api/events
GET  /api/events/{id}
GET  /api/cities
GET  /api/categories
POST /api/search
POST /api/search/natural
GET  /api/recommendations
POST /api/favorites
DELETE /api/favorites/{event_id}
GET  /api/favorites
POST /api/preferences
GET  /api/preferences
POST /api/analytics/events
```

## 10. Docker

Рекомендуемый MVP:

```text
docker-compose
├── backend
├── worker
├── frontend
└── postgres
```

Redis добавлять только при реальной необходимости.

Не нужен Kubernetes.

## 11. Будущая миграция в микросервисы

Если продукт вырастет, первыми кандидатами на выделение будут:
- provider ingestion;
- search/recommendation;
- notifications.

Но в хакатоне физически разделять их не следует.

## 12. Источники документации

- MAX Web Apps: https://dev.max.ru/docs/webapps/introduction
- KudaGo Public API: https://kudago.com/pages/public-api/opisanie-api/
- Timepad API: https://dev.timepad.ru/api/what-api-can/
- Modular Monolith: https://habr.com/ru/companies/dododev/articles/650721/
