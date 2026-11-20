#!/usr/bin/env bash
# 保留入口；参数直接传给Python，不把路径或实验ID拼入代码。
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/check_run_artifacts.py" "$@"
