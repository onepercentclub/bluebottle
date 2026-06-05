#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ci-python-env.sh
source "${script_dir}/ci-python-env.sh"
resolve_ci_python_paths

if [ -n "${GITHUB_WORKSPACE:-}" ] && [ -d "${GITHUB_WORKSPACE}" ]; then
  cd "${GITHUB_WORKSPACE}"
fi

export PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"
eval "$(pyenv init -)"
pyenv shell "${PYTHON_VERSION}"
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"
python -c "import pkg_resources" 2>/dev/null || python -m pip install "setuptools==69.5.1"
