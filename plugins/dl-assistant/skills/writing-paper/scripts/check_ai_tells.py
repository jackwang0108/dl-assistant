"""表达建议扫描；匹配不判断作者身份、诚信或科学质量。

用法: python3 check_ai_tells.py <paper_root>

对 sections/*.tex（剥注释，不剥 math）跑 case-insensitive 正则：
- ai_tell：可能冗余或空泛，命中只作 WARN。
- defensive_write：限定语结合证据判断，只作 WARN——
  按 word-craft 结合事实判断；真实的有限提升或落后可以保留
  （局限该说，但不用道歉式措辞说）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Report, hit, read_lines, relpath, find_main_tex, scan_tex_files

PATTERNS = [
    r"it is worth noting",
    r"it should be noted",
    r"it is important to note",
    r"plays? a (crucial|key|vital|pivotal|central|critical|significant) role",
    r"a testament to",
    r"(rich|intricate) tapestry",
    r"delve(s|d)? into",
    r"in the realm of",
    r"ever-(evolving|changing|growing|expanding)",
    r"in today'?s (world|era|landscape)",
    r"navigat\w* the (landscape|complexit\w+|intricac\w+)",
    r"paradigm shift",
    r"game[- ]chang(er|ing|es)",
    r"in order to",
]

# 这些短语可能准确表达真实限制，只提示审阅，不强制删除或改写。
DEFENSIVE_PATTERNS = [
    r"\bunfortunately\b",
    r"\bregrettably\b",
    r"it is unfortunate",
    r"\bonly (achiev\w+|attain\w+|reach\w+|yield\w+|obtain\w+)",
    r"\bmerely (achiev\w+|attain\w+|reach\w+|obtain\w+)",
    r"limited (improvement|gain|performance|success)",
    r"modest (improvement|gain|performance|result)",
    r"still lags? behind",
    r"remains? (inferior|far behind)",
]

REGS = [re.compile(p, re.IGNORECASE) for p in PATTERNS]
DEFENSIVE_REGS = [re.compile(p, re.IGNORECASE) for p in DEFENSIVE_PATTERNS]


def main():
    if len(sys.argv) != 2:
        print("用法: python3 check_ai_tells.py <paper_root>")
        return 2
    root = sys.argv[1].rstrip("/")
    rep = Report("ai_tells")

    main_tex, problems = find_main_tex(root)
    if main_tex is None:
        rep.unchecked("text_scan", "; ".join(problems))
        return rep.emit()
    files = scan_tex_files(root, main_tex)
    if not files:
        rep.skip("ai_tell", "无 sections/*.tex")
        rep.skip("defensive_write", "无 sections/*.tex")
        rep.emit()
        return 0

    hits = []
    defensive_hits = []
    for path in files:
        lines = read_lines(path)
        if lines is None:
            continue
        disp = relpath(root, path)
        for i, line in enumerate(lines):
            phrases = [m.group(0) for rg in REGS for m in rg.finditer(line)]
            if phrases:
                hits.append(hit(disp, i + 1, "%s" % " / ".join(phrases)))
            defensive = [m.group(0) for rg in DEFENSIVE_REGS for m in rg.finditer(line)]
            if defensive:
                defensive_hits.append(hit(disp, i + 1, "%s" % " / ".join(defensive)))

    if hits:
        rep.warn("expression_review", hits)
    else:
        rep.pass_("ai_tell")
    if defensive_hits:
        rep.warn("qualification_review", defensive_hits)
    else:
        rep.pass_("defensive_write")
    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
