#!/usr/bin/env bash
# check-run-artifacts.sh —— code-paper-experiment 产物验收脚本
#
# 两种模式：
#   run 级（每实验跑完、结果进 results.json 之前）：
#     check-run-artifacts.sh --expdir experiments/<exp_id> [--spec experiments/run-spec.json --exp-id <exp_id>]
#   包级（数据包交 writing-paper 之前）：
#     check-run-artifacts.sh --pkgdir <paper-data-pkg>
#
# 只查机器能查准的客观项：目录契约的存在性、json 可解析性、必需字段、seed 数对账。
# log 完整性（有没有正常结尾/eval 段）与指标合理性归 agent 看（见 SKILL.md Step 5）。
# 输出 markdown Status 表（agent 读 stdout）。查不过 → 不接收，先补/重跑。
#
# 依赖：python3（解析 json）——没有则 json 相关项标 SKIP。

set -uo pipefail

EXPDIR=""
PKGDIR=""
SPEC=""
EXP_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --expdir) EXPDIR="$2"; shift 2 ;;
    --pkgdir) PKGDIR="$2"; shift 2 ;;
    --spec) SPEC="$2"; shift 2 ;;
    --exp-id) EXP_ID="$2"; shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "未知参数: $1（用 -h 看帮助）" >&2; exit 2 ;;
  esac
done

if [[ -z "$EXPDIR" && -z "$PKGDIR" ]]; then
  echo "错误：需要 --expdir（run 级）或 --pkgdir（包级）之一" >&2
  exit 2
fi
if [[ -n "$SPEC" && -z "$EXP_ID" ]]; then
  echo "错误：给 --spec 必须同时给 --exp-id" >&2
  exit 2
fi

HAS_PY=1
command -v python3 >/dev/null 2>&1 || HAS_PY=0

echo ""
echo "## 产物验收结果"
echo ""
echo "| 检查项 | 结果 | 状态 | 备注 |"
echo "|---|---|---|---|"

row() { echo "| $1 | $2 | $3 | $4 |"; }

# json 可解析 + 必需字段检查。$1=文件 $2=逗号分隔的必需顶层字段（可空=只查可解析）
check_json() {
  local f="$1" keys="$2"
  if [[ "$HAS_PY" -eq 0 ]]; then row "$(basename "$f") 可解析" "—" "SKIP" "缺 python3"; return; fi
  python3 - "$f" "$keys" <<'PY'
import json, sys
f, keys = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(f))
except Exception as e:
    print(f"FAIL|json 解析失败：{e}"); sys.exit(0)
missing = [k for k in keys.split(",") if k and k not in d]
if missing:
    print(f"FAIL|缺必需字段：{', '.join(missing)}")
else:
    print("PASS|—")
PY
}

# ============================================================
# run 级：单实验目录契约
# ============================================================
if [[ -n "$EXPDIR" ]]; then
  if [[ ! -d "$EXPDIR" ]]; then
    echo "错误：--expdir 目录不存在：$EXPDIR" >&2
    exit 2
  fi

  # 1. run-spec 条目存在且字段齐（可选，给了 --spec 才查）
  if [[ -n "$SPEC" ]]; then
    if [[ "$HAS_PY" -eq 0 ]]; then
      row "run-spec 条目" "—" "SKIP" "缺 python3"
    elif [[ ! -f "$SPEC" ]]; then
      row "run-spec 条目" "无文件" "FAIL" "$SPEC 不存在"
    else
      python3 - "$SPEC" "$EXP_ID" <<'PY' | while IFS='|' read -r st note; do row "run-spec 条目" "$st" "$st" "$note"; done
import json, sys
spec, eid = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(spec))
except Exception as e:
    print(f"FAIL|run-spec.json 解析失败：{e}"); sys.exit(0)
entry = next((e for e in d.get("experiments", []) if e.get("exp_id") == eid), None)
if entry is None:
    print(f"FAIL|run-spec.json 里没有 {eid} 的条目"); sys.exit(0)
missing = [k for k in ("entry_script", "config_file", "command", "seeds") if k not in entry]
if missing:
    print(f"FAIL|条目缺字段：{', '.join(missing)}")
else:
    cfg = entry["config_file"]
    if "/configs/" not in cfg:
        print(f"WARN|config_file 未指向 configs/ 冻结副本：{cfg}")
    else:
        print("PASS|—")
PY
    fi
  fi

  # 2. configs/ 冻结副本存在且非空
  if [[ -d "$EXPDIR/configs" ]] && find "$EXPDIR/configs" -type f | grep -q .; then
    row "configs/ 冻结副本" "在" "PASS" "$(find "$EXPDIR/configs" -type f | wc -l | tr -d ' ') 个文件"
  else
    row "configs/ 冻结副本" "缺" "FAIL" "实际用的 config 必须冻结副本进目录——repo 原件会被改，不冻结不可回溯"
  fi

  # 3. scripts/ 启动脚本存在且非空
  if [[ -d "$EXPDIR/scripts" ]] && find "$EXPDIR/scripts" -type f | grep -q .; then
    row "scripts/ 启动脚本" "在" "PASS" "$(find "$EXPDIR/scripts" -type f | wc -l | tr -d ' ') 个文件"
  else
    row "scripts/ 启动脚本" "缺" "FAIL" "启动脚本（含完整命令行）必须落盘"
  fi

  # 4. runs/seed-*/ 逐 seed：train.log + metrics.json
  if [[ -d "$EXPDIR/runs" ]]; then
    seed_dirs=$(find "$EXPDIR/runs" -maxdepth 1 -type d -name 'seed-*' | sort)
    if [[ -z "$seed_dirs" ]]; then
      row "runs/seed-*" "无" "FAIL" "runs/ 下没有 seed-<n> 目录"
    else
      n_seeds=0; bad=""; warn=""
      while IFS= read -r sd; do
        n_seeds=$((n_seeds + 1))
        sname=$(basename "$sd")
        [[ -s "$sd/train.log" ]] || bad="$bad $sname:缺train.log"
        if [[ -f "$sd/metrics.json" && "$HAS_PY" -eq 1 ]]; then
          python3 -c "import json;json.load(open('$sd/metrics.json'))" 2>/dev/null || bad="$bad $sname:metrics.json解析失败"
        elif [[ ! -f "$sd/metrics.json" ]]; then
          bad="$bad $sname:缺metrics.json"
        fi
        [[ -f "$sd/eval.log" ]] || warn="$warn $sname:缺eval.log"
      done <<< "$seed_dirs"
      if [[ -z "$bad" ]]; then
        row "runs/seed-* 产物" "${n_seeds} 个 seed 齐" "PASS" "train.log + metrics.json 均在且可解析"
      else
        row "runs/seed-* 产物" "${n_seeds} 个 seed，有缺项" "FAIL" "$(echo $bad | tr ' ' ';' | cut -c1-120)"
      fi
      if [[ -n "$warn" ]]; then
        row "runs/seed-* eval.log" "有缺失" "WARN" "$(echo $warn | tr ' ' ';' | cut -c1-120)"
      fi
      # 5. seed 数 vs run-spec 约定数
      if [[ -n "$SPEC" && "$HAS_PY" -eq 1 && -f "$SPEC" ]]; then
        want=$(python3 -c "
import json
d=json.load(open('$SPEC'))
e=next((x for x in d.get('experiments',[]) if x.get('exp_id')=='$EXP_ID'),{})
print(len(e.get('seeds',[])))" 2>/dev/null || echo "")
        if [[ -n "$want" && "$want" != "0" ]]; then
          if [[ "$n_seeds" -eq "$want" ]]; then
            row "seed 数对账" "${n_seeds}/${want}" "PASS" "—"
          else
            row "seed 数对账" "${n_seeds}/${want}" "WARN" "少于 spec 约定——results.json 的 n_seeds 如实记、notes 写原因、判定降置信"
          fi
        fi
      fi
    fi
  else
    row "runs/seed-* 产物" "无 runs/" "FAIL" "目录契约要求 runs/seed-<n>/{train.log,eval.log,metrics.json}"
  fi

  # 6. results.json 可解析 + 必需字段
  if [[ -f "$EXPDIR/results.json" ]]; then
    res=$(check_json "$EXPDIR/results.json" "exp_id,n_seeds,results,signal_verdict")
    row "results.json" "${res%%|*}" "${res%%|*}" "${res#*|}"
  else
    row "results.json" "缺" "FAIL" "—"
  fi

  # 7. meta.json 可解析
  if [[ -f "$EXPDIR/meta.json" ]]; then
    res=$(check_json "$EXPDIR/meta.json" "experiment_id,type,git_commit")
    row "meta.json" "${res%%|*}" "${res%%|*}" "${res#*|}"
  else
    row "meta.json" "缺" "FAIL" "—"
  fi

  # 8. 报告.md（人读封面）存在
  if [[ -f "$EXPDIR/报告.md" ]]; then
    row "报告.md" "在" "PASS" "人读封面（TL;DR 结论先行）"
  else
    row "报告.md" "缺" "FAIL" "模板见 references/templates/exp-report-template.md"
  fi

  # 9. qualitative：figures/ 非空（spec 里 type=qualitative 才查）
  if [[ -n "$SPEC" && "$HAS_PY" -eq 1 && -f "$SPEC" ]]; then
    is_qual=$(python3 -c "
import json
d=json.load(open('$SPEC'))
e=next((x for x in d.get('experiments',[]) if x.get('exp_id')=='$EXP_ID'),{})
print(1 if e.get('type')=='qualitative' else 0)" 2>/dev/null || echo 0)
    if [[ "$is_qual" == "1" ]]; then
      if [[ -d "$EXPDIR/figures" ]] && find "$EXPDIR/figures" -type f | grep -q .; then
        row "figures/（qualitative）" "在" "PASS" "$(find "$EXPDIR/figures" -type f | wc -l | tr -d ' ') 个文件"
      else
        row "figures/（qualitative）" "缺" "FAIL" "qualitative 实验必须产可视化样本"
      fi
    fi
  fi
fi

# ============================================================
# 包级：数据包交 writing-paper 前
# ============================================================
if [[ -n "$PKGDIR" ]]; then
  if [[ ! -d "$PKGDIR" ]]; then
    echo "错误：--pkgdir 目录不存在：$PKGDIR" >&2
    exit 2
  fi

  # 1. 三个机读产物存在 + 可解析 + 必需字段
  for f in "experiments-actual.json:plan_ref,experiments_actual" \
           "results.json:plan_ref,experiments" \
           "pkg-meta.json:plan_ref,experiments,weights_root"; do
    name="${f%%:*}"; keys="${f#*:}"
    if [[ -f "$PKGDIR/$name" ]]; then
      res=$(check_json "$PKGDIR/$name" "$keys")
      row "$name" "${res%%|*}" "${res%%|*}" "${res#*|}"
    else
      row "$name" "缺" "FAIL" "数据包三件套缺一不可"
    fi
  done

  # 2. 交叉对账：experiments_actual 的每个 exp 在 results.json 有条目；
  #    pkg-meta 里 status=done 的在 results.json 有条目；dropped 的带 reason
  if [[ "$HAS_PY" -eq 1 && -f "$PKGDIR/experiments-actual.json" && -f "$PKGDIR/results.json" && -f "$PKGDIR/pkg-meta.json" ]]; then
    python3 - "$PKGDIR" <<'PY' | while IFS='|' read -r st note; do row "交叉对账" "$st" "$st" "$note"; done
import json, sys
pkg = sys.argv[1]
actual = {e["exp_id"] for e in json.load(open(f"{pkg}/experiments-actual.json"))["experiments_actual"]}
results = {e["exp_id"] for e in json.load(open(f"{pkg}/results.json"))["experiments"]}
meta = json.load(open(f"{pkg}/pkg-meta.json"))["experiments"]
problems = []
for e in actual - results:
    problems.append(f"{e}:actual 有 results 缺")
for m in meta:
    if m.get("status") == "done" and m["exp_id"] not in results:
        problems.append(f"{m['exp_id']}:done 但 results 缺")
    if m.get("status") == "dropped" and not m.get("reason"):
        problems.append(f"{m['exp_id']}:dropped 缺 reason")
if problems:
    print("FAIL|" + "; ".join(problems[:5]))
else:
    print("PASS|actual/results/pkg-meta 三边一致")
PY
  fi

  # 3. results.json 条目必需字段（WP 机械核对项）
  if [[ "$HAS_PY" -eq 1 && -f "$PKGDIR/results.json" ]]; then
    python3 - "$PKGDIR/results.json" <<'PY' | while IFS='|' read -r st note; do row "results 条目字段" "$st" "$st" "$note"; done
import json, sys
exps = json.load(open(sys.argv[1]))["experiments"]
req = ("exp_id", "n_seeds", "signal_verdict", "output_to_paper")
bad = [f"{e.get('exp_id','?')} 缺 {', '.join(k for k in req if k not in e)}" for e in exps if any(k not in e for k in req)]
if bad:
    print("FAIL|" + "; ".join(bad[:5]))
else:
    print(f"PASS|{len(exps)} 个条目字段齐")
PY
  fi

  # 4. pilot/scan-results.json（有 decides_config 实验的批应有）
  if [[ -f "$PKGDIR/pilot/scan-results.json" ]]; then
    res=$(check_json "$PKGDIR/pilot/scan-results.json" "scans")
    row "pilot/scan-results.json" "${res%%|*}" "${res%%|*}" "${res#*|}"
  else
    row "pilot/scan-results.json" "无" "WARN" "本批含超参选定（decides_config）则必须有——WP 敏感性分析素材"
  fi

  # 5. 权重/全量 log 不该在包里
  big=$(find "$PKGDIR" -type f \( -name '*.pt' -o -name '*.pth' -o -name '*.ckpt' -o -name '*.safetensors' -o -name 'train.log' \) 2>/dev/null | head -3)
  if [[ -z "$big" ]]; then
    row "权重/log 不进包" "干净" "PASS" "—"
  else
    row "权重/log 不进包" "混入" "FAIL" "$(printf '%s' "$big" | tr '\n' ';') —— 留 GPU，pkg-meta.json 给指针"
  fi
fi

echo ""
