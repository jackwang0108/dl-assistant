"""共享工具：论文根解析、注释剥离、行读取、检查报告输出。

被 check_*.py 与 run_checks.py 复用；路径一律相对 <paper_root> 解析，与 cwd 无关。
"""
import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# 路径与文件
# ---------------------------------------------------------------------------

def read_lines(path):
    """读文件并逐行剥离 LaTeX 注释；返回行列表，文件不存在返回 None。"""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError as e:
        print("[WARN] 无法读取 %s: %s" % (path, e))
        return None
    return [strip_comments_line(ln.rstrip("\n")) for ln in text.split("\n")]


def strip_comments_line(line):
    """去掉 LaTeX 注释（% 到行尾），正确处理 \\% 转义。

    % 前连续反斜杠数为奇数 -> 转义的字面 %，保留；偶数 -> 注释起点。
    """
    n = len(line)
    i = 0
    while i < n:
        if line[i] == "%":
            j = i - 1
            bs = 0
            while j >= 0 and line[j] == "\\":
                bs += 1
                j -= 1
            if bs % 2 == 0:
                return line[:i].rstrip()
        i += 1
    return line.rstrip()


def tex_files(root, subdir):
    """root/<subdir> 下所有 .tex（排序）；目录不存在返回空列表。"""
    d = os.path.join(root, subdir)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if name.endswith(".tex") and os.path.isfile(p):
            out.append(p)
    return out


def find_main_tex(root):
    """定位主 tex，返回 (path 或 None, 问题列表)。

    顺序：
    1) _draft/config.json 的 main_tex 字段（指向存在则用）；
    2) 根目录唯一 *.tex；
    3) 多个 *.tex 中含 \\documentclass 的那个。
    """
    problems = []
    cfg = os.path.join(root, "_draft", "config.json")
    if os.path.isfile(cfg):
        try:
            with open(cfg, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            return None, ["config.json 解析失败: %s" % e]
        if not isinstance(data, dict):
            return None, ["config.json 须为对象"]
        if isinstance(data, dict):
            mt = data.get("main_tex")
            if isinstance(mt, str) and mt.strip():
                p = os.path.join(root, mt.strip())
                if os.path.isfile(p):
                    return p, problems
                return None, ["config.json 的 main_tex 指向不存在: %s" % mt]
    if not os.path.isdir(root):
        return None, ["论文根不存在或不是目录: %s" % root]
    texs = [os.path.join(root, n) for n in sorted(os.listdir(root))
            if n.endswith(".tex") and os.path.isfile(os.path.join(root, n))]
    if not texs:
        problems.append("根目录无 *.tex，找不到主 tex")
        return None, problems
    if len(texs) == 1:
        return texs[0], problems
    candidates = []
    for p in texs:
        lines = read_lines(p)
        if lines is not None and re.search(r"\\documentclass", "\n".join(lines)):
            candidates.append(p)
    if len(candidates) == 1:
        return candidates[0], problems
    problems.append("无法唯一确定主 tex，请在 config.json 中指定 main_tex")
    return None, problems


def scan_tex_files(root, main_tex):
    """扫描主文件及静态可解析的本地 input/include/subfile，循环引用只读一次。

    不展开宏或条件编译；其他资产需要编译与人工检查。
    """
    out, seen = [], set()
    def visit(path):
        path = os.path.abspath(path)
        if path in seen or not os.path.isfile(path):
            return
        seen.add(path)
        out.append(path)
        lines = read_lines(path) or []
        for match in re.finditer(r"\\(?:input|include|subfile)\s*\{([^{}]+)\}", "\n".join(lines)):
            name = match.group(1).strip()
            if "\\" in name or "#" in name:
                continue
            if not os.path.splitext(name)[1]:
                name += ".tex"
            choices = [os.path.join(root, name), os.path.join(os.path.dirname(path), name)]
            for candidate in choices:
                if os.path.isfile(candidate):
                    visit(candidate)
                    break
    if main_tex:
        visit(main_tex)
    return out


def norm(s):
    """规范化：lowercase + 去空格/下划线/连字符，用于包含匹配。"""
    return re.sub(r"[\s_\-]+", "", s.lower())


def contains_match(a, b):
    """互相包含即算匹配（两侧均为原始写法亦可）。"""
    a, b = norm(a), norm(b)
    return bool(a and b and (a in b or b in a))


def relpath(root, p):
    return os.path.relpath(p, root)


# ---------------------------------------------------------------------------
# 检查报告：PASS/FAIL/WARN/SKIP/UNCHECKED；缺材料不转成通过
# ---------------------------------------------------------------------------

class Report:
    def __init__(self, name):
        self.name = name
        self.items = []  # (status, label, hits, note)

    def add(self, status, label, hits=(), note=""):
        self.items.append((status, label, list(hits), note))

    def pass_(self, label, note=""):
        self.add("PASS", label, (), note)

    def fail(self, label, hits):
        self.add("FAIL", label, hits)

    def warn(self, label, hits):
        self.add("WARN", label, hits)

    def skip(self, label, note=""):
        self.add("SKIP", label, (), note)

    def unchecked(self, label, note=""):
        self.add("UNCHECKED", label, note=note)

    def emit(self):
        """返回1表示错误，3表示未检查完成，0仅表示未发现硬错误。"""
        counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0, "UNCHECKED": 0}
        for status, label, hits, note in self.items:
            line = "[%s] %s" % (status, label)
            if note:
                line += "  (%s)" % note
            print(line)
            for h in hits:
                print("    " + h)
            counts[status] += 1
        print("[SUMMARY] %s: PASS=%d FAIL=%d WARN=%d SKIP=%d UNCHECKED=%d" % (
            self.name, counts["PASS"], counts["FAIL"], counts["WARN"], counts["SKIP"], counts["UNCHECKED"]))
        return 1 if counts["FAIL"] else (3 if counts["UNCHECKED"] else 0)


def hit(path, lineno, snippet):
    return "%s:%d  %s" % (path, lineno, snippet)


def context(line, start, end, pad=60, maxlen=140):
    """取命中附近的上下文片段（压平空白、截断）。"""
    a = max(0, start - pad)
    b = min(len(line), end + pad)
    s = re.sub(r"\s+", " ", line[a:b]).strip()
    if len(s) > maxlen:
        s = s[:maxlen] + "..."
    return s
