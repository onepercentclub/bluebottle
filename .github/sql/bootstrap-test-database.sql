\set ON_ERROR_STOP on

SELECT set_config('bb.test_db_name', :'TEST_DB_NAME', false);
SELECT set_config('bb.test_db_user', :'TEST_DB_USER', false);
SELECT set_config('bb.test_db_password', :'TEST_DB_PASSWORD', false);

DO $$
DECLARE
  role_name text := current_setting('bb.test_db_user');
  role_password text := current_setting('bb.test_db_password');
BEGIN
  IF NOT EXISTS (
    SELECT FROM pg_catalog.pg_roles WHERE rolname = role_name
  ) THEN
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', role_name, role_password);
  END IF;
  EXECUTE format('ALTER ROLE %I WITH SUPERUSER CREATEDB CREATEROLE', role_name);
END
$$;

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_setting('bb.test_db_name')
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS :"TEST_DB_NAME";

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname LIKE current_setting('bb.test_db_name') || '\_%' ESCAPE '\'
  AND pid <> pg_backend_pid();

SELECT format('DROP DATABASE IF EXISTS %I', datname)
FROM pg_database
WHERE datname LIKE current_setting('bb.test_db_name') || '\_%' ESCAPE '\';
\gexec

CREATE DATABASE :"TEST_DB_NAME" OWNER :"TEST_DB_USER";

\c template1

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS unaccent;

\c :TEST_DB_NAME :TEST_DB_USER :PGHOST :PGPORT :TEST_DB_PASSWORD

\i /workspace/testdata.sql

DO $$
DECLARE
  r record;
  max_id bigint;
BEGIN
  FOR r IN
    SELECT
      n.nspname AS schema_name,
      c.relname AS table_name,
      a.attname AS column_name,
      pg_get_serial_sequence(format('%I.%I', n.nspname, c.relname), a.attname) AS seq_name
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_attribute a ON a.attrelid = c.oid
    WHERE c.relkind = 'r'
      AND n.nspname = 'public'
      AND a.attnum > 0
      AND NOT a.attisdropped
      AND a.attname = 'id'
  LOOP
    IF r.seq_name IS NOT NULL THEN
      EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I.%I', r.column_name, r.schema_name, r.table_name) INTO max_id;
      EXECUTE format('SELECT setval(%L, %s, true)', r.seq_name, GREATEST(max_id, 1));
    END IF;
  END LOOP;
END
$$;
