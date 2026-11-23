#!/usr/bin/env bash
# run-long.sh — 长任务 tmux detach 封装（dl-assistant/references/long-run-ops.md 的可执行版）
#
# 用法: run-long.sh <session名> <logdir> '<命令>'
# 例:   run-long.sh ex-myexp-exp1 experiments/exp1/runs 'python train.py --config x.yaml'
#       （命令在调用者的当前目录下执行；要换目录把 cd 写进命令里）
#
# 产物（真相源，见 long-run-ops.md「状态文件契约」）：
#   <logdir>/<session名>.log        stdout + stderr
#   <logdir>/<session名>.EXIT_CODE  终态 sentinel：不存在 = 还在跑；0 成功 / 非 0 失败
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "用法: run-long.sh <session名> <logdir> '<命令>'" >&2
  exit 2
fi

SESSION="$1"
LOGDIR="$2"
CMD="$3"

mkdir -p "$LOGDIR"
LOGDIR_ABS="$(cd "$LOGDIR" && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "session '$SESSION' 已存在（还在跑？）——换个名字，或先查看会话、日志和退出码" >&2
  exit 1
fi

tmux new-session -d -s "$SESSION" \
  "cd $(printf '%q' "$PWD") && ( $CMD ) > $(printf '%q' "$LOGDIR_ABS/$SESSION.log") 2>&1; echo \$? > $(printf '%q' "$LOGDIR_ABS/$SESSION.EXIT_CODE")"

cat <<EOF
已 detach 启动: tmux session '$SESSION'
  查状态: tmux has-session -t '$SESSION' 2>/dev/null && echo RUNNING || echo GONE
  看进展: tail -n 30 '$LOGDIR_ABS/$SESSION.log'
  看终态: cat '$LOGDIR_ABS/$SESSION.EXIT_CODE' 2>/dev/null || echo 未结束
EOF
