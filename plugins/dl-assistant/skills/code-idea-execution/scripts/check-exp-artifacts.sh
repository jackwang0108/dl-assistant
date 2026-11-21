#!/usr/bin/env bash
# check-exp-artifacts.sh —— code-idea-execution 实验产物验收脚本
#
# 两种模式：
#   单实验（每实验跑完、更新台账之前）：
#     check-exp-artifacts.sh --expdir ideas/v<N>-<slug>/experiments/exp-XXX-<name>
#   全量（Step 9 派验收子 agent 之前）：
#     check-exp-artifacts.sh --all ideas/v<N>-<slug>/experiments
#
# 只查机器能查准的客观项：目录契约的存在性、json 可解析性、预登记字段非空、
# 台账对账。log 内容（有没有正常结尾/训练是否病态）归 agent 自己看。
# 输出 markdown Status 表（agent 读 stdout）。查不过 → 先补齐/重跑，再更新台账 / 派验收。
#
# 依赖：python3（解析 json）——没有则 json 相关项标 SKIP。

set -uo pipefail

EXPDIR=""
ALLDIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --expdir) EXPDIR="$2"; shift 2 ;;
    --all) ALLDIR="$2"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "未知参数: $1（用 -h 看帮助）" >&2; exit 2 ;;
  esac
done

if [[ -z "$EXPDIR" && -z "$ALLDIR" ]]; then
  echo "错误：需要 --expdir（单实验）或 --all（全量）之一" >&2
  exit 2
fi

HAS_PY=1
command -v python3 >/dev/null 2>&1 || HAS_PY=0

echo ""
echo "## 实验产物验收结果"
echo ""
echo "| 检查项 | 结果 | 状态 | 备注 |"
echo "|---|---|---|---|"

row() { echo "| $1 | $2 | $3 | $4 |"; }

# 单实验目录契约检查。$1=实验目录 $2=台账文件（可空）
check_one() {
  local d="$1" index="$2"
  local eid; eid=$(basename "$d")

  # 1. meta.json 可解析 + 预登记字段非空（decision_rule / anchor_run 是「不移动球门」的命根）
  if [[ ! -f "$d/meta.json" ]]; then
    row "$eid meta.json" "缺" "FAIL" "—"; return
  fi
  if [[ "$HAS_PY" -eq 0 ]]; then
    row "$eid meta.json" "—" "SKIP" "缺 python3"
    local exp_type="training"
  else
    local meta_res
    meta_res=$(python3 - "$d/meta.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print(f"FAIL|json 解析失败：{e}|training"); sys.exit(0)
missing = [k for k in ("experiment_id", "type", "git_commit") if k not in d]
empty = [k for k in ("decision_rule", "anchor_run") if not d.get(k)]
exp_type = d.get("type", "training")
if missing:
    print(f"FAIL|缺必需字段：{', '.join(missing)}|{exp_type}")
elif empty:
    print(f"FAIL|预登记字段为空：{', '.join(empty)}——开跑前必须写死，跑完补=移动球门|{exp_type}")
else:
    print(f"PASS|—|{exp_type}")
PY
)
    local st note
    st="${meta_res%%|*}"; note="$(echo "$meta_res" | cut -d'|' -f2)"; exp_type="$(echo "$meta_res" | cut -d'|' -f3)"
    row "$eid meta.json（含预登记）" "$st" "$st" "$note"
  fi

  # 2. configs/ 冻结副本（training / ablation 类必需；diagnostic / analysis 类警告级）
  local cfg_need="FAIL"
  [[ "$exp_type" == "diagnostic" || "$exp_type" == "analysis" ]] && cfg_need="WARN"
  if [[ -d "$d/configs" ]] && find "$d/configs" -type f | grep -q .; then
    row "$eid configs/ 冻结副本" "在" "PASS" "$(find "$d/configs" -type f | wc -l | tr -d ' ') 个文件"
  else
    row "$eid configs/ 冻结副本" "缺" "$cfg_need" "实际用的 config 必须冻结副本进目录——repo 原件会被改，不冻结不可回溯"
  fi

  # 3. scripts/ 可复现脚本（内嵌完整命令行）存在且非空
  if [[ -d "$d/scripts" ]] && find "$d/scripts" -type f | grep -q .; then
    row "$eid scripts/ 脚本" "在" "PASS" "$(find "$d/scripts" -type f | wc -l | tr -d ' ') 个文件（自查：脚本内嵌完整命令行）"
  else
    row "$eid scripts/ 脚本" "缺" "FAIL" "可复现脚本（含完整命令行）必须落盘，禁扔 /tmp"
  fi

  # 4. 产物区：training / ablation 查 runs/seed-*；diagnostic / analysis 查 analysis/report.md
  if [[ "$exp_type" == "diagnostic" || "$exp_type" == "analysis" ]]; then
    if [[ -f "$d/analysis/report.md" ]]; then
      row "$eid analysis/ 产物" "在" "PASS" "—"
    else
      row "$eid analysis/ 产物" "缺" "FAIL" "诊断/分析类实验必须产 analysis/report.md（+ data/、figures/ 按需）"
    fi
  else
    if [[ -d "$d/runs" ]]; then
      local seed_dirs; seed_dirs=$(find "$d/runs" -maxdepth 1 -type d -name 'seed-*' | sort)
      if [[ -z "$seed_dirs" ]]; then
        row "$eid runs/seed-*" "无" "FAIL" "runs/ 下没有 seed-<n> 目录"
      else
        local n=0 bad="" warn=""
        while IFS= read -r sd; do
          n=$((n + 1))
          local sname; sname=$(basename "$sd")
          [[ -s "$sd/train.log" ]] || bad="$bad $sname:缺train.log"
          if [[ -f "$sd/metrics.json" && "$HAS_PY" -eq 1 ]]; then
            python3 -c "import json;json.load(open('$sd/metrics.json'))" 2>/dev/null || bad="$bad $sname:metrics.json解析失败"
          elif [[ ! -f "$sd/metrics.json" ]]; then
            bad="$bad $sname:缺metrics.json"
          fi
          [[ -f "$sd/eval.log" ]] || warn="$warn $sname:缺eval.log"
        done <<< "$seed_dirs"
        if [[ -z "$bad" ]]; then
          row "$eid runs/seed-* 产物" "${n} 个 seed 齐" "PASS" "train.log + metrics.json 均在"
        else
          row "$eid runs/seed-* 产物" "${n} 个 seed，有缺项" "FAIL" "$(echo $bad | tr ' ' ';' | cut -c1-120)"
        fi
        if [[ -n "$warn" ]]; then
          row "$eid runs/seed-* eval.log" "有缺失" "WARN" "$(echo $warn | tr ' ' ';' | cut -c1-120)"
        fi
      fi
    else
      row "$eid runs/seed-* 产物" "无 runs/" "FAIL" "目录契约要求 runs/seed-<n>/{train.log,eval.log,metrics.json,checkpoints/}"
    fi
  fi

  # 5. 报告.md（人读封面）存在
  if [[ -f "$d/报告.md" ]]; then
    row "$eid 报告.md" "在" "PASS" "人读封面（TL;DR 结论先行）"
  else
    row "$eid 报告.md" "缺" "FAIL" "模板见 references/exp-report-template.md"
  fi

  # 6. 台账对账：index.json 里有本实验的行
  if [[ -n "$index" && -f "$index" && "$HAS_PY" -eq 1 ]]; then
    local idx_res
    idx_res=$(python3 - "$index" "$eid" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print(f"FAIL|台账 json 解析失败：{e}"); sys.exit(0)
ids = [e.get("experiment_id") for e in d.get("experiments", [])]
print("PASS|—" if sys.argv[2] in ids else f"FAIL|台账 index.json 里没有 {sys.argv[2]} 的行")
PY
)
    row "$eid 台账对账" "${idx_res%%|*}" "${idx_res%%|*}" "${idx_res#*|}"
  fi
}

if [[ -n "$EXPDIR" ]]; then
  if [[ ! -d "$EXPDIR" ]]; then
    echo "错误：--expdir 目录不存在：$EXPDIR" >&2
    exit 2
  fi
  check_one "$EXPDIR" "$(dirname "$EXPDIR")/index.json"
fi

if [[ -n "$ALLDIR" ]]; then
  if [[ ! -d "$ALLDIR" ]]; then
    echo "错误：--all 目录不存在：$ALLDIR" >&2
    exit 2
  fi
  # 台账本身可解析
  if [[ -f "$ALLDIR/index.json" && "$HAS_PY" -eq 1 ]]; then
    python3 -c "import json;json.load(open('$ALLDIR/index.json'))" 2>/dev/null \
      && row "台账 index.json" "可解析" "PASS" "—" \
      || row "台账 index.json" "解析失败" "FAIL" "—"
  elif [[ ! -f "$ALLDIR/index.json" ]]; then
    row "台账 index.json" "缺" "FAIL" "—"
  fi
  found=0
  for d in "$ALLDIR"/exp-*/; do
    [[ -d "$d" ]] || continue
    found=1
    check_one "${d%/}" "$ALLDIR/index.json"
  done
  [[ "$found" -eq 0 ]] && row "实验目录" "无" "WARN" "$ALLDIR 下没有 exp-* 目录"
fi

echo ""
