#!/usr/bin/env bash
# 用法：run-long.sh <会话名> <日志目录> '<命令>'
# 命令在调用目录中由 Bash 执行。每次尝试使用独立会话名。
# 日志和退出码保存在 <日志目录>/<会话名>.log 和 <会话名>.EXIT_CODE。
# 启动信息保存在 <日志目录>/.<会话名>.launch/。缺少退出码时需核对会话和日志。
set -euo pipefail

if [[ "$#" -ne 3 ]]; then
  printf '%s\n' "用法：run-long.sh <会话名> <日志目录> '<命令>'" >&2
  exit 2
fi

session="$1"
log_dir="$2"
task_command="$3"

if [[ ! "$session" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ || -z "$log_dir" || ! "$task_command" =~ [^[:space:]] ]]; then
  printf '%s\n' '会话名须以字母或数字开头，只能含字母、数字、下划线和连字符。日志目录与命令须非空。' >&2
  exit 2
fi
if ! command -v tmux >/dev/null 2>&1; then
  printf '%s\n' '找不到 tmux，任务未启动。' >&2
  exit 2
fi

work_dir="$(pwd -P)"
if [[ "$log_dir" != /* ]]; then
  log_dir="$work_dir/$log_dir"
fi
umask 077
mkdir -p -- "$log_dir"
log_dir_abs="$(cd -- "$log_dir" && pwd -P)"
log_file="$log_dir_abs/$session.log"
exit_file="$log_dir_abs/$session.EXIT_CODE"
launch_dir="$log_dir_abs/.$session.launch"
launch_script="$launch_dir/run.sh"

if tmux has-session -t "=$session" 2>/dev/null; then
  printf '会话已存在：%s。先检查该会话和任务记录，再为新尝试选择新名称。\n' "$session" >&2
  exit 1
fi

for record in "$log_file" "$exit_file" "$launch_dir"; do
  if [[ -e "$record" || -L "$record" ]]; then
    printf '任务记录已存在：%s。请为新尝试使用新会话名。\n' "$record" >&2
    exit 1
  fi
done

# 独占目录防止并发启动覆盖同一尝试，也保留启动失败时的证据。
if ! mkdir -- "$launch_dir"; then
  printf '无法创建独占启动目录：%s。请核对权限和是否已有同名尝试。\n' "$launch_dir" >&2
  exit 1
fi

{
  printf 'work_dir=%q\nlog_file=%q\nexit_file=%q\nexit_tmp=%q\n' \
    "$work_dir" "$log_file" "$exit_file" "$launch_dir/EXIT_CODE.tmp"
  printf 'bash_path=%q\ntask_command=%q\n' "$BASH" "$task_command"
  cat <<'RUN_TASK'

task_umask="$(umask)"
umask 077
if {
  umask "$task_umask"
  cd -- "$work_dir" && "$bash_path" -o pipefail -c "$task_command"
} >"$log_file" 2>&1; then
  result=0
else
  result=$?
fi

umask 077
if ! printf '%s\n' "$result" >"$exit_tmp" || ! mv -- "$exit_tmp" "$exit_file"; then
  printf '无法保存退出码：%s\n' "$exit_file" >>"$log_file"
  exit 1
fi
exit "$result"
RUN_TASK
} >"$launch_script"

# 有些启动错误只输出到 stderr，要求 tmux 返回实际创建的会话名。
if ! started_session="$(tmux new-session -d -P -F '#{session_name}' -s "$session" "$BASH" "$launch_script")" ||
   [[ "$started_session" != "$session" ]]; then
  printf 'tmux 未确认创建会话。已保留启动记录：%s\n' "$launch_dir" >&2
  exit 1
fi

printf 'tmux 已接受启动请求：%s\n' "$session"
printf '  启动记录：%s\n' "$launch_dir"
printf '  查会话：tmux has-session -t %q\n' "=$session"
printf '  看日志：tail -n 30 %q\n' "$log_file"
printf '  查退出码：cat %q\n' "$exit_file"
printf '%s\n' '缺少退出码时，结合会话、进程和日志核对状态。'
