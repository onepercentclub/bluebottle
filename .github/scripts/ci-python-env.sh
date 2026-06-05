setup_py_sha() {
  python - <<'PY'
import hashlib
from pathlib import Path
print(hashlib.sha256(Path("setup.py").read_bytes()).hexdigest()[:12])
PY
}

resolve_ci_python_paths() {
  PYTHON_VERSION="${PYTHON_VERSION:-3.11.4}"
  PYENV_ROOT="${PYENV_ROOT:-/home/github_actions/.pyenv}"
  PIP_EXTRA="${PIP_EXTRA:-test}"

  if [ -z "${VENV_DIR:-}" ]; then
    local major minor sha
    IFS=. read -r major minor _ <<< "${PYTHON_VERSION}"
    sha="$(setup_py_sha)"
    VENV_DIR="/home/github_actions/venvs/bluebottle-py${major}${minor}-${sha}"
    if [ "${PIP_EXTRA}" != "test" ]; then
      VENV_DIR="${VENV_DIR}-${PIP_EXTRA}"
    fi
  fi

  export PYTHON_VERSION PYENV_ROOT VENV_DIR PIP_EXTRA
}
