#!/usr/bin/env bash
# submission-check.sh —— writing-paper-submission 机器自检脚本
#
# 只跑机器真能查准的客观项，输出 markdown Status 表（agent 读 stdout 放进就绪报告）：
#   页数 / 断引用 / 重 label / 字体嵌入 / metadata
# tex 源判断（双盲泄露、~ 前缀）与页面观感（越界/图糊/乱码）不在此查——
# 那些是 agent 读 tex + 渲染 PNG 看的活（见 SKILL.md Step 2/3）。
#
# 两种模式（二选一，都不给则跳过身份相关项）：
#   submission（默认）：--double-blind 时 Author 应空、非空 FAIL（Title 非空只 INFO——hyperref 默认写 pdftitle，不算泄露）
#   camera-ready：      --camera-ready 时反向——metadata 空则 WARN（作者信息应补回）
#
# 用法：
#   submission-check.sh --pdf <PDF> [--log <LaTeX log>]
#                        [--page-limit <n>] [--main-pages <n>]
#                        [--double-blind | --camera-ready]
#
# 页数口径：venue 只限正文时传 --main-pages（正文页数，从 PDF 定位 refs 起始页算）；
# 不传则拿 PDF 总页数对照 --page-limit，备注里注明口径。
# 部分输入：缺 --log → 跳过断引用/重 label；缺 --pdf → 报错退出。
# 退出码：参数错 exit 2；正常跑完 exit 0（发现的问题在输出里，不靠退出码表达）。

set -uo pipefail

PDF=""
LOG=""
PAGE_LIMIT=""
MAIN_PAGES=""
DOUBLE_BLIND=0
CAMERA_READY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pdf) PDF="$2"; shift 2 ;;
    --log) LOG="$2"; shift 2 ;;
    --page-limit) PAGE_LIMIT="$2"; shift 2 ;;
    --main-pages) MAIN_PAGES="$2"; shift 2 ;;
    --double-blind) DOUBLE_BLIND=1; shift ;;
    --camera-ready) CAMERA_READY=1; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "未知参数: $1（用 -h 看帮助）" >&2; exit 2 ;;
  esac
done

if [[ -z "$PDF" || ! -f "$PDF" ]]; then
  echo "错误：需要 --pdf 指向存在的 PDF 文件" >&2
  exit 2
fi
if [[ "$DOUBLE_BLIND" -eq 1 && "$CAMERA_READY" -eq 1 ]]; then
  echo "错误：--double-blind 与 --camera-ready 互斥（前者是 submission 模式，后者是定稿模式）" >&2
  exit 2
fi

has() { command -v "$1" >/dev/null 2>&1; }

echo ""
echo "## 机器自检结果"
echo ""
echo "| 检查项 | 工具 | 结果 | 状态 | 备注 |"
echo "|---|---|---|---|---|"

# ---- 1. 页数（对照 venue-contract 的口径与上限）----
if has pdfinfo; then
  pages=$(pdfinfo "$PDF" 2>/dev/null | awk '/^Pages:/ {print $2; exit}')
  if [[ -n "$pages" && "$pages" =~ ^[0-9]+$ ]]; then
    if [[ -n "$MAIN_PAGES" ]]; then
      judged="$MAIN_PAGES"
      scope="正文 ${MAIN_PAGES} 页（全 PDF 共 ${pages} 页，refs/appendix 不计）"
    else
      judged="$pages"
      scope="全 PDF 总页数口径——若 venue 只限正文，应传 --main-pages"
    fi
    if [[ -n "$PAGE_LIMIT" && "$judged" -gt "$PAGE_LIMIT" ]]; then
      echo "| 页数 | pdfinfo | ${judged} 页 | FAIL | 超上限 ${PAGE_LIMIT} 页（超 $((judged - PAGE_LIMIT)) 页）；${scope} |"
    elif [[ -n "$PAGE_LIMIT" ]]; then
      echo "| 页数 | pdfinfo | ${judged} 页 | PASS | 上限 ${PAGE_LIMIT} 页内；${scope} |"
    else
      echo "| 页数 | pdfinfo | ${judged} 页 | INFO | 未给 --page-limit，对照 venue-contract.md 自查；${scope} |"
    fi
  else
    echo "| 页数 | pdfinfo | 解析失败 | WARN | pdfinfo 未返回页数 |"
  fi
else
  echo "| 页数 | pdfinfo | — | SKIP | 装 poppler（brew install poppler）|"
fi

# ---- 2. 断引用（需 LaTeX 编译日志）----
if [[ -n "$LOG" && -f "$LOG" ]]; then
  undefs=$(grep -iE "LaTeX Warning.*(Citation|Reference).*undefined" "$LOG" 2>/dev/null || true)
  if [[ -z "$undefs" ]]; then
    echo "| 断引用 | grep log | 0 处 | PASS | — |"
  else
    n=$(printf '%s\n' "$undefs" | grep -c .)
    sample=$(printf '%s\n' "$undefs" | head -2 | tr '\n' ';' | cut -c1-100)
    echo "| 断引用 | grep log | ${n} 处 | FAIL | ${sample} |"
  fi
else
  echo "| 断引用 | grep log | — | SKIP | 缺 --log（需 overleaf 编译的 output.log）|"
fi

# ---- 3. 重 label（需 LaTeX 编译日志；编译器自己会报 multiply defined）----
if [[ -n "$LOG" && -f "$LOG" ]]; then
  dups=$(grep -iE "multiply.?defined" "$LOG" 2>/dev/null || true)
  if [[ -z "$dups" ]]; then
    echo "| 重 label | grep log | 0 处 | PASS | — |"
  else
    n=$(printf '%s\n' "$dups" | grep -c .)
    sample=$(printf '%s\n' "$dups" | head -2 | tr '\n' ';' | cut -c1-100)
    echo "| 重 label | grep log | ${n} 处 | FAIL | ${sample} |"
  fi
else
  echo "| 重 label | grep log | — | SKIP | 缺 --log |"
fi

# ---- 4. 字体嵌入（未嵌会导致提交系统/审稿人显示乱）----
if has pdffonts; then
  # pdffonts 有列陷阱：type 列 "Type 1" 含空格、object ID 可有可无，
  # 按固定列号取 emb 会错位。改找"连续三个 yes/no"（emb/sub/uni），第一个是 emb。
  notemb=$(pdffonts "$PDF" 2>/dev/null | tail -n +3 | awk '
    { for (i=1;i<=NF-2;i++) if ($i~/^(yes|no)$/ && $(i+1)~/^(yes|no)$/ && $(i+2)~/^(yes|no)$/) { if ($i!="yes") print $1; break } }' || true)
  if [[ -z "$notemb" ]]; then
    echo "| 字体嵌入 | pdffonts | 全嵌 | PASS | — |"
  else
    echo "| 字体嵌入 | pdffonts | 未嵌 | FAIL | $(printf '%s\n' "$notemb" | tr '\n' ',') 未嵌入 |"
  fi
else
  echo "| 字体嵌入 | pdffonts | — | SKIP | 装 poppler |"
fi

# ---- 5. metadata 身份字段（双模式反向）----
# pdfinfo 对空字段也打印 "Author:" 行——必须只取冒号后有内容的，否则干净 PDF 误报。
# 双盲只查 Author：Title 非空是 hyperref 默认写 pdftitle 的正常行为（标题不是身份信息），
# Creator/Producer 基本被下面的过滤器覆盖（编译器占位）——后两者都不该判泄露。
if has pdfinfo; then
  author=$(pdfinfo "$PDF" 2>/dev/null | awk -F: '/^Author:/ && $2 ~ /[^ \t]/' || true)
  author=$(printf '%s\n' "$author" | grep -viE 'latex|tex|overleaf' || true)  # 排除编译器默认占位（不算身份信息）
  hastitle=$(pdfinfo "$PDF" 2>/dev/null | awk -F: '/^Title:/ && $2 ~ /[^ \t]/{print "yes"; exit}' || true)
  if [[ "$CAMERA_READY" -eq 1 ]]; then
    if [[ -z "$author" ]]; then
      echo "| metadata | pdfinfo | 空 | WARN | camera-ready 应补回作者信息——查 hyperref 的 pdfauthor/pdftitle（非强制，建议补）|"
    else
      echo "| metadata | pdfinfo | 已填 | PASS | — |"
    fi
  elif [[ "$DOUBLE_BLIND" -eq 1 ]]; then
    if [[ -n "$author" ]]; then
      echo "| 双盲-metadata | pdfinfo | 泄露 | FAIL | $(printf '%s\n' "$author" | tr '\n' ';') |"
    elif [[ -n "$hastitle" ]]; then
      echo "| 双盲-metadata | pdfinfo | 已清 | INFO | Author 空；Title 非空是 hyperref 默认写 pdftitle——标题不是身份信息，无需处理 |"
    else
      echo "| 双盲-metadata | pdfinfo | 已清 | PASS | — |"
    fi
  else
    echo "| metadata | — | 跳过 | INFO | 未给 --double-blind / --camera-ready，不查身份字段 |"
  fi
else
  echo "| metadata | pdfinfo | — | SKIP | 装 poppler |"
fi

echo ""
