#!/usr/bin/env bash
set -euxo pipefail
if [ -n "${GITHUB_WORKSPACE:-}" ] && [ -d "${GITHUB_WORKSPACE}" ]; then
  cd "${GITHUB_WORKSPACE}"
fi

PYTHON_VERSION="${PYTHON_VERSION:-3.11.4}"
PYENV_ROOT="${PYENV_ROOT:-/home/github_actions/.pyenv}"
VENV_DIR="${VENV_DIR:-/home/github_actions/venvs/bluebottle-py311}"
PIP_EXTRA="${PIP_EXTRA:-test}"
export PIP_DEFAULT_TIMEOUT="${PIP_DEFAULT_TIMEOUT:-120}"
export PIP_RETRIES="${PIP_RETRIES:-10}"

export PYENV_ROOT
export PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"
eval "$(pyenv init -)"
pyenv install -s "${PYTHON_VERSION}"
pyenv global "${PYTHON_VERSION}"
python --version | grep -F "Python ${PYTHON_VERSION}"

mkdir -p "$(dirname "$VENV_DIR")"
if [ ! -x "$VENV_DIR/bin/python" ] || ! "$VENV_DIR/bin/python" -c "import sys; v=tuple(int(x) for x in '${PYTHON_VERSION}'.split('.')); sys.exit(0 if sys.version_info[:3]==v else 1)"; then
  rm -rf "$VENV_DIR"
  python -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

{
  echo "PYENV_ROOT=${PYENV_ROOT}"
  echo "VENV_DIR=${VENV_DIR}"
} >> "${GITHUB_ENV}"

NEW_SHA="$(python - <<'PY'
import hashlib
from pathlib import Path
digest = hashlib.sha256()
for name in ("setup.py", "requirements-ci-bootstrap.txt"):
    digest.update(Path(name).read_bytes())
print(digest.hexdigest())
PY
)"
STAMP="${VENV_DIR}/.deps-setup_py-${PIP_EXTRA}.sha"
LEGACY_STAMP="${VENV_DIR}/.deps-setup_py.sha"
OLD_SHA="$(cat "${STAMP}" 2>/dev/null || true)"
if [ -z "${OLD_SHA}" ] && [ "${PIP_EXTRA}" = "test" ]; then
  OLD_SHA="$(cat "${LEGACY_STAMP}" 2>/dev/null || true)"
fi

deps_ok() {
  python -c "import django" 2>/dev/null || return 1
  if [ "${PIP_EXTRA}" = "dev" ]; then
    python -c "import flake8" 2>/dev/null || return 1
  fi
  return 0
}

if [ "${OLD_SHA}" = "${NEW_SHA}" ] && deps_ok; then
  echo "${NEW_SHA}" > "${STAMP}"
  echo "Dependencies up to date; skipping pip install."
  exit 0
fi

if deps_ok && [ -z "${OLD_SHA}" ]; then
  echo "${NEW_SHA}" > "${STAMP}"
  echo "Venv ready (no stamp yet); skipping pip install."
  exit 0
fi

pip_install() {
  python -m pip install --upgrade "pip==25.3" "setuptools==69.5.1" wheel
  python -m pip install -r requirements-ci-bootstrap.txt
  python -m pip install -e ".[${PIP_EXTRA}]"
}

for attempt in 1 2 3; do
  if pip_install; then
    echo "${NEW_SHA}" > "${STAMP}"
    exit 0
  fi
  echo "pip install failed (attempt ${attempt}/3)"
  if [ "${attempt}" -eq 3 ]; then
    exit 1
  fi
  sleep $((attempt * 15))
done
