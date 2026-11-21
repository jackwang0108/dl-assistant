"""AI 腔 + 自我削弱表达硬正则检查（零误报清单）。

用法: python3 check_ai_tells.py <paper_root>

对 sections/*.tex（剥注释，不剥 math）跑 case-insensitive 正则：
- ai_tell：AI 腔/填充语，命中即 FAIL。
- defensive_write：预防性自我削弱表达（防御性写作指纹），命中即 FAIL——
  按 word-craft 原则 4 改写成边界声明或删除；诚实披露局限不属此类
  （局限该说，但不用道歉式措辞说）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Report, hit, read_lines, relpath, tex_files

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

# 预防性自我削弱表达（防御性写作指纹）。入选标准：几乎只用于
# 道歉式示弱的措辞；诚实的边界声明有别的说法，不在这里。
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

    files = tex_files(root, "sections")
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
        rep.fail("ai_tell", hits)
    else:
        rep.pass_("ai_tell")
    if defensive_hits:
        rep.fail("defensive_write", defensive_hits)
    else:
        rep.pass_("defensive_write")
    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
