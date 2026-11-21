"""数字诚实 gate。

用法: python3 check_numbers.py <paper_root>

两种模式，取决于 _draft/canonical-values.json 是否存在且非空：
- 模式 A（白名单存在）：prose 小数/百分比不在白名单 -> FAIL suspicious_number
  （按小数位容差匹配：prose 有 n 位小数时 |prose - 白名单| < 0.5*10^-n 算命中；
    白名单存 87.31 时 prose 写 87.3 也算命中）；跳过表格检查。
- 模式 B（白名单不存在）：prose 小数/百分比（排除后）-> FAIL number_without_data；
  另查 tables/*.tex 数据格（剥表头 + 行首标签列）出现小数/百分比
  -> FAIL fabricated_number_in_result_table（数据没到时结果表只许 --/TBD）。

prose 抽取：剥注释 -> 删 display/浮动环境整块（equation/align/gather/multline/
table/tabular/figure）-> 删行内 math（$...$、\\[...\\]）-> 删 \\cite/\\ref/\\label/
\\input 参数。排除规则：① 数字后紧跟单位；② 前 40 字符窗口内有超参 cue。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Report, hit, read_lines, relpath, tex_files

# display/浮动环境块起止 token
TOKEN_RE = re.compile(
    r"\\begin\{(equation|align|gather|multline|table|tabular|figure)\*?\}"
    r"|\\end\{(equation|align|gather|multline|table|tabular|figure)\*?\}"
    r"|\\\[|\\\]|\$\$",
    re.IGNORECASE)

CMD_ARG_RE = re.compile(
    r"\\(?:citep|citet|citealp|citeyear|cite|eqref|autoref|cref|Cref|ref|label|input)"
    r"(?:\[[^\]]*\])?\{[^}]*\}")
INLINE_MATH_RE = re.compile(r"\$[^$\n]*\$")

DEC_RE = re.compile(r"\d+\.\d+")
PCT_RE = re.compile(r"\d+(?:\.\d+)?\s*\\?%")
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# 排除规则 ①：数字后紧跟单位
UNIT_RE = re.compile(
    r"\s*(?:GHz|MHz|kHz|Hz|ms|mm|cm|MB|GB|TB|dB|fps|GFLOPs?|pixels?)\b",
    re.IGNORECASE)
# 排除规则 ②：前 40 字符窗口内有超参 cue（lr 用词边界，比裸 "lr " 更稳）
CUE_RE = re.compile(
    r"learning rate|dropout|weight decay|batch size|temperature|epoch|\blr\b",
    re.IGNORECASE)


def display_mask(lines):
    """标记被 display/浮动环境整块覆盖的行（含 begin/end 行）。"""
    n = len(lines)
    deleted = [False] * n
    stack = []          # 栈内: env 名 / "$$" / "["
    dollar_open = False  # $$ 开合计数
    for i, line in enumerate(lines):
        if stack:
            deleted[i] = True
        line_open = False
        for m in TOKEN_RE.finditer(line):
            if m.group(1):                       # \begin{env}
                stack.append(m.group(1))
                line_open = True
            elif m.group(2):                     # \end{env}
                if stack:
                    stack.pop()
            elif m.group(0) == r"\[":
                # \\[3pt] 是换行+可选参数，不是 display math
                if m.start() > 0 and line[m.start() - 1] == "\\":
                    continue
                stack.append("[")
                line_open = True
            elif m.group(0) == r"\]":
                if stack and stack[-1] == "[":
                    stack.pop()
            else:                                # $$
                dollar_open = not dollar_open
                if dollar_open:
                    stack.append("$$")
                    line_open = True
                else:
                    if stack and stack[-1] == "$$":
                        stack.pop()
        if line_open:
            deleted[i] = True
    return deleted


def _overlaps(start, end, spans):
    return any(s1 < end and start < s2 for s1, s2 in spans)


def _excluded(line, start, end):
    """排除规则 ① 数字后紧跟单位 ② 前 40 字符超参 cue。"""
    if UNIT_RE.match(line, end):
        return True
    before = line[max(0, start - 40):start]
    if CUE_RE.search(before):
        return True
    return False


def _ndec(text):
    m = re.search(r"\.(\d+)", text)
    return len(m.group(1)) if m else 0


def prose_numbers(root, files):
    """抽取 prose 小数/百分比（已过排除规则），yield (disp, ln, text, val, ndec)。"""
    for path in files:
        lines = read_lines(path)
        if lines is None:
            continue
        disp = relpath(root, path)
        mask = display_mask(lines)
        for i, line in enumerate(lines):
            if mask[i]:
                continue
            l = INLINE_MATH_RE.sub("", line)
            l = CMD_ARG_RE.sub("", l)
            if not l:
                continue
            pct_spans = [(m.start(), m.end()) for m in PCT_RE.finditer(l)]
            for m in PCT_RE.finditer(l):
                if _excluded(l, m.start(), m.end()):
                    continue
                val_txt = NUM_RE.match(m.group(0)).group(0)
                yield (disp, i + 1, m.group(0), float(val_txt), _ndec(val_txt))
            for m in DEC_RE.finditer(l):
                if _overlaps(m.start(), m.end(), pct_spans):
                    continue
                if _excluded(l, m.start(), m.end()):
                    continue
                yield (disp, i + 1, m.group(0), float(m.group(0)), _ndec(m.group(0)))


def check_tables(root, tables):
    """结果表数据格小数/百分比检查（剥 \\midrule 前表头 + 行首标签列）。"""
    hits = []
    for path in tables:
        lines = read_lines(path)
        if lines is None:
            continue
        disp = relpath(root, path)
        started = False
        for i, line in enumerate(lines):
            if not started and ("\\midrule" in line or "\\hline" in line):
                started = True
                continue
            if not started:
                continue
            amp = line.find("&")
            if amp == -1:
                continue
            cells = line[amp + 1:]
            pct_spans = [(m.start(), m.end()) for m in PCT_RE.finditer(cells)]
            for m in PCT_RE.finditer(cells):
                hits.append(hit(disp, i + 1, "数据格出现百分比 %s" % m.group(0)))
            for m in DEC_RE.finditer(cells):
                if _overlaps(m.start(), m.end(), pct_spans):
                    continue
                hits.append(hit(disp, i + 1, "数据格出现小数 %s" % m.group(0)))
    return hits


def load_whitelist(root):
    """返回白名单 float 列表；不存在/为空/解析失败返回 None（模式 B）。"""
    path = os.path.join(root, "_draft", "canonical-values.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("[WARN] canonical-values.json 解析失败: %s（按无白名单处理）" % e)
        return None
    if not isinstance(data, list) or not data:
        return None
    vals = []
    for e in data:
        v = e.get("value") if isinstance(e, dict) else e
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    return vals or None


def whitelist_hit(val, ndec, wl):
    tol = 0.5 * 10 ** (-ndec)
    return any(abs(val - w) < tol for w in wl)


def main():
    if len(sys.argv) != 2:
        print("用法: python3 check_numbers.py <paper_root>")
        return 2
    root = sys.argv[1].rstrip("/")
    rep = Report("numbers")

    secs = tex_files(root, "sections")
    tables = tex_files(root, "tables")
    wl = load_whitelist(root)

    if wl:
        # 模式 A：白名单存在
        if not secs:
            rep.skip("suspicious_number", "无 sections/*.tex")
        else:
            hits = [hit(d, l, "%s（白名单外）" % txt)
                    for d, l, txt, _v, _n in prose_numbers(root, secs)
                    if not whitelist_hit(_v, _n, wl)]
            if hits:
                rep.fail("suspicious_number", hits)
            else:
                rep.pass_("suspicious_number", "模式 A（白名单 %d 项）" % len(wl))
        rep.skip("fabricated_number_in_result_table",
                 "白名单存在，表格视为已从真数据填")
    else:
        # 模式 B：白名单不存在
        if not secs:
            rep.skip("number_without_data", "无 sections/*.tex")
        else:
            hits = [hit(d, l, "%s（无数据来源的数字）" % txt)
                    for d, l, txt, _v, _n in prose_numbers(root, secs)]
            if hits:
                rep.fail("number_without_data", hits)
            else:
                rep.pass_("number_without_data")
        if not tables:
            rep.skip("fabricated_number_in_result_table", "无 tables/*.tex")
        else:
            thits = check_tables(root, tables)
            if thits:
                rep.fail("fabricated_number_in_result_table", thits)
            else:
                rep.pass_("fabricated_number_in_result_table")

    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
