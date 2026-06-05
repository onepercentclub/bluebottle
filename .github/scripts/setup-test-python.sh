#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ci-python-env.sh
source "${script_dir}/ci-python-env.sh"

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

venv_has_required_packages() {
  python -c "import django, pkg_resources" 2>/dev/null || return 1
  if [ "${PIP_EXTRA}" = "dev" ]; then
    python -c "import flake8" 2>/dev/null || return 1
  fi
}

venv_is_ready() {
  ! venv_needs_recreate && venv_has_required_packages
}

ensure_setuptools() {
  python -c "import pkg_resources" 2>/dev/null || python -m pip install "setuptools==69.5.1"
}

install_editable_package() {
  python -m pip install --upgrade "pip==25.3" "setuptools==69.5.1" wheel
  python -m pip install -e ".[${PIP_EXTRA}]"
}

install_editable_package_with_retry() {
  local attempt=1

  while [ "${attempt}" -le 3 ]; do
    if install_editable_package; then
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
  enter_repo_root
  resolve_ci_python_paths
  setup_pyenv
  setup_venv
  write_github_env

  if venv_is_ready; then
    ensure_setuptools
    echo "venv ${VENV_DIR} ready; skipping pip install."
    return 0
  fi

  install_editable_package_with_retry
}

main "$@"
