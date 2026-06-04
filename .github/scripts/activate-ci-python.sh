#!/usr/bin/env bash
set -euo pipefail
export PYENV_ROOT="${PYENV_ROOT:-/home/github_actions/.pyenv}"
export PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"
eval "$(pyenv init -)"
pyenv shell "${PYTHON_VERSION:-3.11.4}"
source "${VENV_DIR:-/home/github_actions/venvs/bluebottle-py311}/bin/activate"
