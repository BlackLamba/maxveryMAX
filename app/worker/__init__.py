"""Background worker: ingestion и нормализация событий в PostgreSQL.

Правило архитектуры: worker пишет в БД, backend читает из БД.
Worker никогда не вызывает backend API и не вызывается из него.
"""