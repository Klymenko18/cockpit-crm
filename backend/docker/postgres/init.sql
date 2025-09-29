-- backend/docker/postgres/init.sql
-- Потрібно для EXCLUDE USING gist на SCD2 (no-overlap)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- pg_trgm не використовуємо зараз — забираємо для простоти.
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Таймзона: покладаємось на Django (USE_TZ=True, TIME_ZONE=UTC)
-- ALTER SYSTEM SET timezone TO 'UTC';  -- не потрібно
