#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON_EXE="${PYTHON_EXE:-/home/vullar/miniconda3/envs/utils/bin/python}"
if [[ -n "${CPP_SIMULATOR:-}" ]]; then
  CPP_SIMULATOR="${CPP_SIMULATOR}"
elif [[ -x "${REPO_ROOT}/simulator" ]]; then
  CPP_SIMULATOR="${REPO_ROOT}/simulator"
elif [[ -x "${REPO_ROOT}/../simulator" ]]; then
  CPP_SIMULATOR="${REPO_ROOT}/../simulator"
else
  CPP_SIMULATOR="${REPO_ROOT}/simulator"
fi

if [[ ! -x "${CPP_SIMULATOR}" ]]; then
  echo "[ERROR] C++ simulator not found or not executable: ${CPP_SIMULATOR}"
  echo "Build first (project default): cd ${REPO_ROOT} && autoconf && ./configure && make"
  echo "Or build directly in repo root: g++ -std=c++11 -O3 -I\"\$CONDA_PREFIX/include\" cpp_sources/*.cpp -L\"\$CONDA_PREFIX/lib\" -Wl,-rpath,\"\$CONDA_PREFIX/lib\" -lhdf5_cpp -lhdf5 -lhdf5_hl -o simulator"
  exit 2
fi

exec "${PYTHON_EXE}" "${REPO_ROOT}/scripts/equivalence_check.py" \
  --repo-root "${REPO_ROOT}" \
  --cpp-simulator "${CPP_SIMULATOR}" \
  "$@"
