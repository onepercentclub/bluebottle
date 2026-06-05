#!/usr/bin/env bash
set -euo pipefail

PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:?PGPORT is required}"
PG_CLI_IMAGE="${PG_CLI_IMAGE:-postgis/postgis:14-3.3}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
ESHOST="${ESHOST:-}"
ESPORT="${ESPORT:-}"
WAIT_ATTEMPTS="${WAIT_ATTEMPTS:-60}"
WAIT_SLEEP_SECONDS="${WAIT_SLEEP_SECONDS:-2}"

pg_run() {
  docker run --rm -i --network host \
    -e "PGPASSWORD=${PGPASSWORD:-}" \
    "${PG_CLI_IMAGE}" \
    "$@"
}

postgres_ready() {
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_run pg_isready \
    -h "${PGHOST}" -p "${PGPORT}" -U postgres >/dev/null 2>&1
}

elasticsearch_ready() {
  curl -fsS \
    "http://${ESHOST}:${ESPORT}/_cluster/health?wait_for_status=yellow&timeout=5s" \
    | grep -q '"timed_out":false'
}

services_ready() {
  postgres_ready || return 1
  if [ -n "${ESHOST}" ] && [ -n "${ESPORT}" ]; then
    elasticsearch_ready || return 1
  fi
}

main() {
  if [ -n "${ESHOST}" ] && [ -n "${ESPORT}" ]; then
    echo "Waiting for Postgres on ${PGHOST}:${PGPORT} and Elasticsearch on ${ESHOST}:${ESPORT}"
  else
    echo "Waiting for Postgres on ${PGHOST}:${PGPORT}"
  fi

  for _ in $(seq 1 "${WAIT_ATTEMPTS}"); do
    if services_ready; then
      return 0
    fi
    sleep "${WAIT_SLEEP_SECONDS}"
  done

  echo "Required services did not become ready"
  return 1
}

main "$@"
