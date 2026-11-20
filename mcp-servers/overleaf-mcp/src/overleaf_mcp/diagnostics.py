"""Separate server outcome, available evidence and LaTeX diagnostics."""

import re


def parse_log(text, stream="output.log"):
    diagnostics = []
    for number, line in enumerate(text.splitlines(), 1):
        error = bool(
            re.search(
                r"^!|Emergency stop|Fatal error|No pages of output|no output PDF|out of memory|\bKilled\b|timed out",
                line,
                re.I,
            )
        )
        warning = bool(
            re.search(
                r"LaTeX Warning|Package .+ Warning|Overfull|Underfull|undefined references|undefined citations|Please.*(?:rerun|Biber)",
                line,
                re.I,
            )
        )
        positioned = re.search(r"([^\s:]+\.(?:tex|sty|cls)):(\d+):\s*(.*)", line)
        if positioned and re.search(r"error", positioned[3], re.I):
            error = True
        if not error and not warning:
            continue
        input_line = re.search(r"(?:input line|at lines?)\s+(\d+)", line)
        diagnostics.append(
            {
                "severity": "error" if error else "warning",
                "stream": stream,
                "log_line": number,
                "message": line[:2000],
                "source_file": positioned[1] if positioned else None,
                "source_line": int(positioned[2])
                if positioned
                else int(input_line[1])
                if input_line
                else None,
                "source_path_trust": "reported_by_compiler_not_a_local_file_instruction",
            }
        )
    return diagnostics


def classify(response, log=None, stderr=None):
    diagnostics = parse_log(log or "") + parse_log(stderr or "", "output.stderr")
    raw = str(response.get("status", "unknown")).lower()
    stats = response.get("stats") or {}
    count = stats.get("latexmk-errors")
    failure = (
        raw in ("failure", "failed", "error", "timeout", "timedout", "compile-error")
        or (isinstance(count, (int, float)) and count > 0)
        or any(d["severity"] == "error" for d in diagnostics)
    )
    if failure:
        status = "failed"
    elif raw != "success" or not log:
        status = "unknown"
    elif any(d["severity"] == "warning" for d in diagnostics):
        status = "warnings"
    elif not any(f.get("path") == "output.pdf" for f in response.get("outputFiles", [])):
        status = "unknown"
    else:
        status = "clean"
    return status, diagnostics
