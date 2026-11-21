"""论文写作检查总入口（体检式，不是流水线门禁——全跑完再汇总）。

用法: python3 run_checks.py <paper_root> [all|labels|citations|ai_tells|numbers]

子检查用 subprocess 调用（脚本路径相对本文件解析，与 cwd 无关），透传其输出；
内置 venue 硬合规检查（_draft/venue-contract.json）：
- mandatory_sections: 在全部 .tex（根 + sections/ + tables/）里找 \\section{<名>}
  （case-insensitive）或 sections/ 下同名 .tex 或 \\input 引用，找不到 -> FAIL
- citation_style == "numeric" 时全文出现 \\citep/\\citet -> FAIL（风格不一致）

结尾打印汇总表；任一检查有 FAIL -> exit 1，全绿 -> exit 0。
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (Report, contains_match, find_main_tex, hit, read_lines,
                     relpath, scan_tex_files)

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = {
    "labels": "check_labels.py",
    "citations": "check_citations.py",
    "ai_tells": "check_ai_tells.py",
    "numbers": "check_numbers.py",
}
ORDER = ["labels", "citations", "ai_tells", "numbers"]

SECTION_RE = re.compile(r"\\section\*?\{([^}]*)\}", re.IGNORECASE)
INPUT_RE = re.compile(r"\\input\{([^}]*)\}")


def _section_present(name, root, files):
    nname = name.strip()
    # ① \\section{<名>}（case-insensitive）
    for p in files:
        lines = read_lines(p)
        if lines is None:
            continue
        for line in lines:
            for m in SECTION_RE.finditer(line):
                if contains_match(m.group(1), nname):
                    return True
    # ② sections/ 下有对应名字的 .tex 文件
    for p in files:
        if os.path.basename(os.path.dirname(p)) == "sections":
            base = os.path.splitext(os.path.basename(p))[0]
            if contains_match(base, nname):
                return True
    # ③ \\input 引用（如 \\input{sections/introduction}）
    for p in files:
        lines = read_lines(p)
        if lines is None:
            continue
        for line in lines:
            for m in INPUT_RE.finditer(line):
                if contains_match(m.group(1), nname):
                    return True
    return False


def venue_check(root):
    rep = Report("venue")
    path = os.path.join(root, "_draft", "venue-contract.json")
    if not os.path.isfile(path):
        rep.skip("missing_mandatory_section", "无 venue-contract.json")
        rep.skip("citation_style_numeric", "无 venue-contract.json")
        return rep
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        rep.skip("missing_mandatory_section", "venue-contract.json 解析失败: %s" % e)
        rep.skip("citation_style_numeric", "venue-contract.json 解析失败: %s" % e)
        return rep
    if not isinstance(data, dict):
        data = {}

    main_tex, _ = find_main_tex(root)
    files = scan_tex_files(root, main_tex)

    ms = data.get("mandatory_sections")
    missing = []
    if isinstance(ms, list):
        for name in ms:
            if isinstance(name, str) and name.strip():
                if not _section_present(name, root, files):
                    missing.append(name.strip())
    if missing:
        rep.fail("missing_mandatory_section",
                 ["mandatory section 缺失: %s" % n for n in missing])
    else:
        rep.pass_("missing_mandatory_section")

    style = data.get("citation_style")
    if isinstance(style, str) and style.strip().lower() == "numeric":
        hits = []
        for p in files:
            lines = read_lines(p)
            if lines is None:
                continue
            disp = relpath(root, p)
            for i, line in enumerate(lines):
                for m in re.finditer(r"\\citep|\\citet", line):
                    hits.append(hit(disp, i + 1, m.group(0)))
        if hits:
            rep.fail("citation_style_numeric", hits)
        else:
            rep.pass_("citation_style_numeric", "style=numeric，无 \\citep/\\citet")
    else:
        rep.skip("citation_style_numeric",
                 "venue-contract.json 未声明 citation_style=numeric")

    return rep


def main():
    if len(sys.argv) not in (2, 3):
        print("用法: python3 run_checks.py <paper_root> [all|labels|citations|ai_tells|numbers]")
        return 2
    root = sys.argv[1].rstrip("/")
    mode = sys.argv[2] if len(sys.argv) == 3 else "all"
    if mode not in CHECKS and mode != "all":
        print("未知检查: %s（可选: all|labels|citations|ai_tells|numbers）" % mode)
        return 2
    todo = ORDER if mode == "all" else [mode]

    rows = []  # (name, PASS, FAIL, WARN, SKIP, rc)
    for name in todo:
        script = os.path.join(HERE, CHECKS[name])
        if not os.path.isfile(script):
            print("[WARN] 找不到子脚本 %s" % script)
            rows.append((name, 0, 1, 0, 0, 1))
            continue
        p = subprocess.run([sys.executable, script, root],
                           stdout=subprocess.PIPE, text=True)
        sys.stdout.write(p.stdout)
        sys.stdout.flush()
        counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
        for ln in p.stdout.splitlines():
            m = re.match(r"^\[(PASS|FAIL|WARN|SKIP)\]", ln)
            if m:
                counts[m.group(1)] += 1
        if p.returncode != 0 and counts["FAIL"] == 0:
            counts["FAIL"] += 1  # 脚本异常退出也视为该检查失败
        rows.append((name, counts["PASS"], counts["FAIL"],
                     counts["WARN"], counts["SKIP"], p.returncode))

    rep = venue_check(root)
    rc_venue = rep.emit()
    vc = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
    for status, _l, _h, _n in rep.items:
        vc[status] += 1
    rows.append(("venue", vc["PASS"], vc["FAIL"], vc["WARN"], vc["SKIP"], rc_venue))

    # ---- 汇总 ----
    print()
    print("[SUMMARY TABLE]")
    print("%-11s %5s %5s %5s %5s" % ("check", "PASS", "FAIL", "WARN", "SKIP"))
    tot = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
    any_fail = False
    for name, npass, nfail, nwarn, nskip, rc in rows:
        print("%-11s %5d %5d %5d %5d" % (name, npass, nfail, nwarn, nskip))
        tot["PASS"] += npass
        tot["FAIL"] += nfail
        tot["WARN"] += nwarn
        tot["SKIP"] += nskip
        if rc != 0:
            any_fail = True
    print("-" * 33)
    print("[OVERALL] PASS=%d FAIL=%d WARN=%d SKIP=%d%s" % (
        tot["PASS"], tot["FAIL"], tot["WARN"], tot["SKIP"],
        "  => FAIL (exit 1)" if any_fail else "  => 全绿 (exit 0)"))
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
