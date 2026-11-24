#!/usr/bin/env bash
# File/record checks only; exit 0 = no structural failures, 1 = failures, 2 = usage/dependency error.
set -uo pipefail
if ! command -v python3 >/dev/null 2>&1; then
  echo "需要 python3 才能检查 JSON；未检查不能视为通过。" >&2
  exit 2
fi
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)" || exit 2
exec python3 -B "$SCRIPT_DIR/check_exp_artifacts.py" "$@"
