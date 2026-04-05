-- db-query 示例数据：填充默认库 postgres（与 test.rest / 契约示例中的 users 查询一致）
-- 执行方式示例：
--   psql "postgres://postgres:postgres@127.0.0.1:5432/postgres" -f fixtures/seed.sql
--   或：docker exec -i dbquery_postgres_1 psql -U postgres -d postgres -v ON_ERROR_STOP=1 < fixtures/seed.sql

SET client_encoding = 'UTF8';

BEGIN;

CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS users_email_key ON public.users (email);

DELETE FROM public.users;

INSERT INTO public.users (email, display_name, created_at) VALUES
    ('alice@example.com', 'Alice', TIMESTAMPTZ '2026-01-05 08:00:00+00'),
    ('bob@example.com', 'Bob', TIMESTAMPTZ '2026-01-10 09:30:00+00'),
    ('carol@example.com', 'Carol', TIMESTAMPTZ '2026-02-01 12:00:00+00'),
    ('dave@other.org', 'Dave', TIMESTAMPTZ '2026-02-15 14:20:00+00'),
    ('eve@example.com', 'Eve', TIMESTAMPTZ '2026-03-01 16:45:00+00'),
    ('frank@example.com', 'Frank', TIMESTAMPTZ '2026-03-20 18:00:00+00');

COMMIT;
