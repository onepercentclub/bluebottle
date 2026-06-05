#!/usr/bin/env bash
set -euo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.11.4}"
PYENV_ROOT="${PYENV_ROOT:-/home/github_actions/.pyenv}"
VENV_DIR="${VENV_DIR:-/home/github_actions/venvs/bluebottle-py311}"
PIP_EXTRA="${PIP_EXTRA:-test}"
PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-120}"
PIP_RETRIES="${PIP_RETRIES:-10}"
export PIP_DEFAULT_TIMEOUT PIP_RETRIES

enter_repo_root() {
  if [ -n "${GITHUB_WORKSPACE:-}" ] && [ -d "${GITHUB_WORKSPACE}" ]; then
    cd "${GITHUB_WORKSPACE}"
  fi
}

setup_pyenv() {
  export PYENV_ROOT
  export PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"
  eval "$(pyenv init -)"
  pyenv install -s "${PYTHON_VERSION}"
  pyenv global "${PYTHON_VERSION}"
  python --version | grep -F "Python ${PYTHON_VERSION}"
}

venv_needs_recreate() {
  if [ ! -x "${VENV_DIR}/bin/python" ]; then
    return 0
  fi
  if "${VENV_DIR}/bin/python" -c "
import sys
expected = tuple(int(part) for part in '${PYTHON_VERSION}'.split('.'))
sys.exit(0 if sys.version_info[:3] == expected else 1)
"; then
    return 1
  fi
  return 0
}

setup_venv() {
  mkdir -p "$(dirname "${VENV_DIR}")"
  if venv_needs_recreate; then
    rm -rf "${VENV_DIR}"
    python -m venv "${VENV_DIR}"
  fi
  # shellcheck source=/dev/null
  source "${VENV_DIR}/bin/activate"
}

write_github_env() {
  {
    echo "PYENV_ROOT=${PYENV_ROOT}"
    echo "VENV_DIR=${VENV_DIR}"
  } >> "${GITHUB_ENV}"
}

setup_py_sha() {
  python - <<'PY'
import hashlib
from pathlib import Path
print(hashlib.sha256(Path("setup.py").read_bytes()).hexdigest())
PY
}

read_stamp() {
  local stamp_file="${1}"
  local legacy_stamp_file="${VENV_DIR}/.deps-setup_py.sha"
  local stamp=""

  stamp="$(cat "${stamp_file}" 2>/dev/null || true)"
  if [ -z "${stamp}" ] && [ "${PIP_EXTRA}" = "test" ]; then
    stamp="$(cat "${legacy_stamp_file}" 2>/dev/null || true)"
  fi
  printf '%s' "${stamp}"
}

write_stamp() {
  printf '%s\n' "${2}" > "${1}"
}

venv_has_required_packages() {
  python -c "import django, pkg_resources" 2>/dev/null || return 1
  if [ "${PIP_EXTRA}" = "dev" ]; then
    python -c "import flake8" 2>/dev/null || return 1
  fi
}

ensure_setuptools() {
  python -c "import pkg_resources" 2>/dev/null || python -m pip install "setuptools==69.5.1"
}

deps_are_current() {
  local setup_sha="${1}"
  local stamp_file="${2}"
  local cached_sha=""

  cached_sha="$(read_stamp "${stamp_file}")"
  [ "${cached_sha}" = "${setup_sha}" ] && venv_has_required_packages
}

install_editable_package() {
  python -m pip install --upgrade "pip==25.3" "setuptools==69.5.1" wheel
  python -m pip install -e ".[${PIP_EXTRA}]"
}

install_editable_package_with_retry() {
  local setup_sha="${1}"
  local stamp_file="${2}"
  local attempt=1

  while [ "${attempt}" -le 3 ]; do
    if install_editable_package; then
      write_stamp "${stamp_file}" "${setup_sha}"
      return 0
    fi
    echo "pip install failed (attempt ${attempt}/3)"
    if [ "${attempt}" -eq 3 ]; then
      return 1
    fi
    sleep $((attempt * 15))
    attempt=$((attempt + 1))
  done
}

main() {
  local setup_sha stamp_file

  enter_repo_root
  setup_pyenv
  setup_venv
  write_github_env

  setup_sha="$(setup_py_sha)"
  stamp_file="${VENV_DIR}/.deps-setup_py-${PIP_EXTRA}.sha"

  if deps_are_current "${setup_sha}" "${stamp_file}"; then
    ensure_setuptools
    write_stamp "${stamp_file}" "${setup_sha}"
    echo "setup.py unchanged; skipping pip install."
    return 0
  fi

  install_editable_package_with_retry "${setup_sha}" "${stamp_file}"
}

main "$@"
