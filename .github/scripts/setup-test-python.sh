#!/usr/bin/env bash
set -euxo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.11.4}"
PYENV_ROOT="${PYENV_ROOT:-/home/github_actions/.pyenv}"
VENV_DIR="${VENV_DIR:-/home/github_actions/venvs/bluebottle-py311}"
PIP_EXTRA="${PIP_EXTRA:-test}"

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
if [ "$(cat "${STAMP}" 2>/dev/null || true)" != "${NEW_SHA}" ] || ! python -c "import django" 2>/dev/null; then
  python -m pip install --upgrade pip setuptools wheel
  python -m pip install -r requirements-ci-bootstrap.txt
  python -m pip install -e ".[${PIP_EXTRA}]"
  echo "${NEW_SHA}" > "${STAMP}"
else
  echo "Dependencies up to date; skipping pip install."
fi
