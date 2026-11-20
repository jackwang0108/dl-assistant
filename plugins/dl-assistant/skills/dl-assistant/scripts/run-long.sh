#!/usr/bin/env bash
# run-long.sh — 长任务 tmux detach 封装（dl-assistant/references/long-run-ops.md 的可执行版）
#
# 用法: run-long.sh <session名> <logdir> '<命令>'
# 例:   run-long.sh ex-myexp-exp1 experiments/exp1/runs 'python train.py --config x.yaml'
#       （命令在调用者的当前目录下执行；要换目录把 cd 写进命令里）
#
# 产物（真相源，见 long-run-ops.md「状态文件契约」）：
#   <logdir>/<session名>.log        stdout + stderr
#   <logdir>/<session名>.EXIT_CODE  终态记录：缺失 = 状态未知；0/非0是命令退出码
#   <logdir>/.<session名>.launch/   独占启动记录；每次attempt使用新名称
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "用法: run-long.sh <session名> <logdir> '<命令>'" >&2
  exit 2
fi

SESSION="$1"
LOGDIR="$2"
CMD="$3"

if [[ ! "$SESSION" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] || [[ -z "$CMD" ]]; then
  echo "session名只能用字母、数字、下划线和连字符，且命令不能为空。" >&2
  exit 2
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "缺少tmux；任务未启动。" >&2
  exit 2
fi

if tmux has-session -t "=$SESSION" 2>/dev/null; then
  echo "session '$SESSION' 已存在（还在跑？）——换个名字，或先只读三连查状态" >&2
  exit 1
fi

umask 077
mkdir -p "$LOGDIR"
LOGDIR_ABS="$(cd "$LOGDIR" && pwd)"
LAUNCH_DIR="$LOGDIR_ABS/.$SESSION.launch"
if [[ -e "$LOGDIR_ABS/$SESSION.log" || -L "$LOGDIR_ABS/$SESSION.log" ||
      -e "$LOGDIR_ABS/$SESSION.EXIT_CODE" || -L "$LOGDIR_ABS/$SESSION.EXIT_CODE" ]] ||
   ! mkdir "$LAUNCH_DIR" 2>/dev/null; then
  echo "已有同名任务记录；保留现场，请为新attempt使用新名称。" >&2
  exit 1
fi

{
  printf 'cd %q || exit 1\n' "$PWD"
  printf 'set -o pipefail\n(\n%s\n) > %q 2>&1\n' "$CMD" "$LOGDIR_ABS/$SESSION.log"
  printf 'result=$?\nprintf "%%s\\n" "$result" > %q && mv %q %q\n' \
    "$LAUNCH_DIR/EXIT_CODE.tmp" "$LAUNCH_DIR/EXIT_CODE.tmp" "$LOGDIR_ABS/$SESSION.EXIT_CODE"
} > "$LAUNCH_DIR/run.sh"

if ! tmux new-session -d -s "$SESSION" "bash $(printf '%q' "$LAUNCH_DIR/run.sh")"; then
  echo "tmux启动失败；保留启动记录，任务状态需核查。" >&2
  exit 1
fi

cat <<EOF
已 detach 启动: tmux session '$SESSION'
  查状态: tmux has-session -t '=$SESSION' 2>/dev/null && echo RUNNING || echo GONE
  看进展: tail -n 30 '$LOGDIR_ABS/$SESSION.log'
  看终态: cat '$LOGDIR_ABS/$SESSION.EXIT_CODE' 2>/dev/null || echo 状态未知，需核查进程和日志
EOF
