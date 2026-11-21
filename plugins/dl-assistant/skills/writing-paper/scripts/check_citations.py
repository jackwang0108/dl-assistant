"""引用完整性检查。

用法: python3 check_citations.py <paper_root>

- FAIL cite_without_entry        : 正文 \\cite 了 refs.bib 没有的 key
- WARN orphan_entry              : refs.bib 有条目但正文从未引用
- _draft/references.json 存在时（list 或 {entries:[...]}）：
    FAIL cite_without_registration : 正文引用的 key 未登记
    FAIL registration_incomplete   : 登记条目缺 claim 或 section（或为空）
    FAIL section_mismatch          : 登记 section 与 \\cite 实际位置不一致（规范化后互相包含即匹配）
    INFO needs_human_verify        : 列出需人工复核的 cite_key
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (Report, contains_match, find_main_tex, hit, read_lines,
                     relpath, scan_tex_files)

CITE_RE = re.compile(
    r"\\(?:citep|citet|citealp|citeyear|cite)(?:\[[^\]]*\])?\{([^}]*)\}")
BIB_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
NON_KEY_TYPES = {"comment", "preamble", "string"}


def extract_cites(root, files):
    """返回 {key: [(disp, lineno), ...]}。"""
    cites = {}
    for path in files:
        lines = read_lines(path)
        if lines is None:
            continue
        disp = relpath(root, path)
        for i, line in enumerate(lines):
            for m in CITE_RE.finditer(line):
                for key in (k.strip() for k in m.group(1).split(",")):
                    if not key:
                        continue
                    cites.setdefault(key, []).append((disp, i + 1))
    return cites


def bib_keys(root):
    path = os.path.join(root, "refs.bib")
    lines = read_lines(path)
    if lines is None:
        return None
    keys = []
    for line in lines:
        for m in BIB_ENTRY_RE.finditer(line):
            typ, key = m.group(1).lower(), m.group(2).strip()
            if typ not in NON_KEY_TYPES:
                keys.append(key)
    return keys


def section_of(path, root, main_tex):
    """\\cite 实际位置的节名近似：sections/x.tex -> "x"，主 tex -> "main"。"""
    if os.path.abspath(path) == os.path.abspath(main_tex):
        return "main"
    return os.path.splitext(os.path.basename(path))[0]


def load_references(root):
    """返回 (path 或 None, entries 列表)。"""
    path = os.path.join(root, "_draft", "references.json")
    if not os.path.isfile(path):
        return None, []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("[WARN] references.json 解析失败: %s（按不存在处理）" % e)
        return None, []
    if isinstance(data, list):
        return path, data
    if isinstance(data, dict):
        return path, data.get("entries", [])
    return path, []


def main():
    if len(sys.argv) != 2:
        print("用法: python3 check_citations.py <paper_root>")
        return 2
    root = sys.argv[1].rstrip("/")
    rep = Report("citations")

    main_tex, problems = find_main_tex(root)
    if main_tex is None:
        rep.fail("main_tex_not_found", problems)
        rep.emit()
        return 1
    files = scan_tex_files(root, main_tex)
    cites = extract_cites(root, files)

    # ---- refs.bib ----
    bib = bib_keys(root)
    if bib is None:
        rep.skip("cite_without_entry", "无 refs.bib")
        rep.skip("orphan_entry", "无 refs.bib")
    else:
        bset = set(bib)
        missing = [k for k in cites if k not in bset]
        if missing:
            rep.fail("cite_without_entry",
                     [hit(*cites[k][0], "\\cite{%s} 在 refs.bib 中无条目" % k)
                      for k in sorted(missing)])
        else:
            rep.pass_("cite_without_entry")
        orphan = [k for k in bset if k not in cites]
        if orphan:
            rep.warn("orphan_entry",
                     ["refs.bib: %s 全文未被引用" % k for k in sorted(orphan)])
        else:
            rep.pass_("orphan_entry")

    # ---- _draft/references.json ----
    refpath, entries = load_references(root)
    if refpath is None:
        rep.skip("cite_without_registration", "无 references.json")
        rep.skip("registration_incomplete", "无 references.json")
        rep.skip("section_mismatch", "无 references.json")
    else:
        registered = {}
        for e in entries:
            if not isinstance(e, dict):
                continue
            k = e.get("cite_key")
            if isinstance(k, str) and k.strip():
                registered[k.strip()] = e

        unreg = [k for k in cites if k not in registered]
        if unreg:
            rep.fail("cite_without_registration",
                     [hit(*cites[k][0], "\\cite{%s} 未在 references.json 登记" % k)
                      for k in sorted(unreg)])
        else:
            rep.pass_("cite_without_registration")

        incomplete = []
        for k, e in sorted(registered.items()):
            claim = e.get("claim")
            sec = e.get("section")
            if not (isinstance(claim, str) and claim.strip()) or \
               not (isinstance(sec, str) and sec.strip()):
                incomplete.append(k)
        if incomplete:
            rep.fail("registration_incomplete",
                     ["cite_key=%s 缺 claim 或 section（或为空）" % k
                      for k in incomplete])
        else:
            rep.pass_("registration_incomplete")

        mism = []
        for k, e in sorted(registered.items()):
            sec = e.get("section")
            if not (isinstance(sec, str) and sec.strip()):
                continue  # 缺 section 已由 registration_incomplete 覆盖
            if k not in cites:
                continue
            actuals = set(section_of(p, root, main_tex) for p, _ in cites[k])
            if not any(contains_match(sec, a) for a in actuals):
                mism.append((k, sec, cites[k][0]))
        if mism:
            rep.fail("section_mismatch",
                     [hit(d, l, "\\cite{%s} 登记 section=%s，实际出现在 %s"
                          % (k, sec, d)) for k, sec, (d, l) in mism])
        else:
            rep.pass_("section_mismatch")

        for k in sorted(registered):
            if registered[k].get("needs_human_verify") in (True, 1, "true", "True", "1"):
                print("[INFO] needs_human_verify: %s" % k)

    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
