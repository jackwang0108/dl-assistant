"""label/\\ref 纪律检查。

用法: python3 check_labels.py <paper_root>

扫描主 tex + sections/*.tex + tables/*.tex（剥注释后）：
- FAIL undefined_ref : \\ref/\\eqref/\\autoref/\\cref/\\Cref 指向不存在的 \\label
- WARN orphan_label  : 定义了 \\label 但全文无引用
- FAIL bare_number   : 裸编号 "Figure N" 等（非 \\ref、非 \\label 参数内）
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (Report, find_main_tex, hit, read_lines, relpath,
                     scan_tex_files)

LABEL_RE = re.compile(r"\\label(?:\[[^\]]*\])?\{([^}]+)\}")
REF_RE = re.compile(r"\\(?:eqref|autoref|cref|Cref|ref)\{([^}]+)\}")
BARE_RE = re.compile(r"\b(?:Figure|Table|Section|Equation|Algorithm)\s+\d")
# 命令参数开括号：用于排除落在 \\ref{...}/\\label{...} 参数内的裸编号
CMD_OPEN_RE = re.compile(
    r"\\(?:eqref|autoref|cref|Cref|ref|label)(?:\[[^\]]*\])?\{")


def _cmd_arg_spans(line):
    spans = []
    for m in CMD_OPEN_RE.finditer(line):
        start = m.end()
        end = line.find("}", start)
        if end != -1:
            spans.append((start, end))
    return spans


def _inside_any(pos, spans):
    for a, b in spans:
        if a <= pos < b:
            return True
    return False


def main():
    if len(sys.argv) != 2:
        print("用法: python3 check_labels.py <paper_root>")
        return 2
    root = sys.argv[1].rstrip("/")
    rep = Report("labels")

    main_tex, problems = find_main_tex(root)
    if main_tex is None:
        rep.fail("main_tex_not_found", problems)
        rep.emit()
        return 1
    files = scan_tex_files(root, main_tex)

    labels = {}       # label -> (disp, lineno) 首次定义处
    used = set()      # 被引用过的 label
    ref_hits = []     # undefined ref
    bare_hits = []

    # 第一遍：收集全部 \\label（跨文件，先定义后使用）
    for path in files:
        lines = read_lines(path)
        if lines is None:
            continue
        disp = relpath(root, path)
        for i, line in enumerate(lines):
            for m in LABEL_RE.finditer(line):
                lab = m.group(1).strip()
                labels.setdefault(lab, (disp, i + 1))

    # 第二遍：查 \\ref 族与裸编号
    for path in files:
        lines = read_lines(path)
        if lines is None:
            continue
        disp = relpath(root, path)
        for i, line in enumerate(lines):
            ln = i + 1
            for m in REF_RE.finditer(line):
                for key in (k.strip() for k in m.group(1).split(",")):
                    if not key:
                        continue
                    used.add(key)
                    if key not in labels:
                        ref_hits.append((disp, ln, key, m.group(0)))
            spans = _cmd_arg_spans(line)
            for m in BARE_RE.finditer(line):
                if _inside_any(m.start(), spans):
                    continue
                bare_hits.append((disp, ln, m.group(0)))

    if ref_hits:
        rep.fail("undefined_ref",
                 [hit(d, l, "%s -> 未定义: %s" % (snippet, key))
                  for d, l, key, snippet in ref_hits])
    else:
        rep.pass_("undefined_ref")

    orphan = [(d, l, lab) for lab, (d, l) in sorted(labels.items()) if lab not in used]
    if orphan:
        rep.warn("orphan_label",
                 [hit(d, l, "\\label{%s} 全文无引用" % lab) for d, l, lab in orphan])
    else:
        rep.pass_("orphan_label")

    if bare_hits:
        rep.fail("bare_number",
                 [hit(d, l, "%s （裸编号，应用 \\ref）" % snip) for d, l, snip in bare_hits])
    else:
        rep.pass_("bare_number")

    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
