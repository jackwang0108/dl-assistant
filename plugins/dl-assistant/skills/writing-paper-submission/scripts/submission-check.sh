#!/usr/bin/env bash
# 保留旧入口；只读观察与有限规则比较，不执行提交或修改材料。
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/submission_check.py" "$@"
