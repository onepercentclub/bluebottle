#!/usr/bin/env bash
set -euo pipefail

PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:?PGPORT is required}"
PG_CLI_IMAGE="${PG_CLI_IMAGE:-postgis/postgis:14-3.3}"
TEST_DB_NAME="${TEST_DB_NAME:-test_bluebottle_test}"
TEST_DB_USER="${TEST_DB_USER:-testuser}"
TEST_DB_PASSWORD="${TEST_DB_PASSWORD:-password}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
WORKSPACE="${GITHUB_WORKSPACE:-$(pwd)}"

pg_run() {
  docker run --rm -i --network host \
    -e "PGPASSWORD=${PGPASSWORD:-}" \
    -v "${WORKSPACE}:/workspace:ro" \
    "${PG_CLI_IMAGE}" \
    "$@"
}

ensure_test_role() {
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_run psql \
    -h "${PGHOST}" -p "${PGPORT}" -U postgres -d postgres <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT FROM pg_catalog.pg_roles WHERE rolname = 'testuser'
  ) THEN
    CREATE ROLE testuser LOGIN PASSWORD 'password';
  END IF;
END
$$;
ALTER ROLE testuser WITH SUPERUSER CREATEDB CREATEROLE;
SQL
}

drop_main_test_database() {
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_run psql \
    -h "${PGHOST}" -p "${PGPORT}" -U postgres -d postgres <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${TEST_DB_NAME}'
  AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS ${TEST_DB_NAME};
SQL
}

drop_parallel_test_databases() {
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_run psql \
    -h "${PGHOST}" -p "${PGPORT}" -U postgres -d postgres <<SQL
DO $$
DECLARE
  db record;
BEGIN
  FOR db IN
    SELECT datname
    FROM pg_database
    WHERE datname LIKE '${TEST_DB_NAME}\_%' ESCAPE '\'
  LOOP
    EXECUTE format(
      'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %L AND pid <> pg_backend_pid()',
      db.datname
    );
    EXECUTE format('DROP DATABASE IF EXISTS %I', db.datname);
  END LOOP;
END
$$;
SQL
}

create_test_database() {
  PGPASSWORD="${TEST_DB_PASSWORD}" pg_run createdb \
    -h "${PGHOST}" -p "${PGPORT}" -U "${TEST_DB_USER}" "${TEST_DB_NAME}"
}

install_template_extensions() {
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_run psql \
    -h "${PGHOST}" -p "${PGPORT}" -U postgres -d template1 <<'SQL'
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS unaccent;
SQL
}

load_test_data() {
  PGPASSWORD="${TEST_DB_PASSWORD}" pg_run psql \
    -h "${PGHOST}" -p "${PGPORT}" -U "${TEST_DB_USER}" -d "${TEST_DB_NAME}" \
    -f /workspace/testdata.sql
}

reset_serial_sequences() {
  PGPASSWORD="${TEST_DB_PASSWORD}" pg_run psql \
    -h "${PGHOST}" -p "${PGPORT}" -U "${TEST_DB_USER}" -d "${TEST_DB_NAME}" <<'SQL'
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
SQL
}

main() {
  ensure_test_role
  drop_main_test_database
  drop_parallel_test_databases
  create_test_database
  install_template_extensions
  load_test_data
  reset_serial_sequences
}

main "$@"
