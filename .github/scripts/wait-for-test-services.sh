#!/usr/bin/env bash
set -euo pipefail

ESHOST="${ESHOST:-}"
ESPORT="${ESPORT:-}"
WAIT_ATTEMPTS=60
WAIT_SLEEP_SECONDS=2

elasticsearch_ready() {
  curl -fsS \
    "http://${ESHOST}:${ESPORT}/_cluster/health?wait_for_status=yellow&timeout=5s" \
    | grep -q '"timed_out":false'
}

main() {
  if [ -z "${ESHOST}" ] || [ -z "${ESPORT}" ]; then
    echo "Postgres readiness is handled by the service health check; no extra wait needed."
    return 0
  fi

  echo "Waiting for Elasticsearch on ${ESHOST}:${ESPORT}"
  for _ in $(seq 1 "${WAIT_ATTEMPTS}"); do
    if elasticsearch_ready; then
      return 0
    fi
    sleep "${WAIT_SLEEP_SECONDS}"
  done

  echo "Elasticsearch did not become ready"
  return 1
}

main "$@"
