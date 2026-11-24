"""Separate server outcome, available evidence and LaTeX diagnostics."""

import re

ERROR = re.compile(
    r"^\s*!|Emergency stop|Fatal error|No pages of output|no output PDF|out of memory|"
    r"\bKilled\b|timed out|(?:^|\s)(?:ERROR|FATAL)\s+-\s|"
    r"\bI couldn't open (?:database|style|file)|\bI found no \\(?:bibdata|bibstyle) command",
    re.I,
)
WARNING = re.compile(
    r"LaTeX Warning|Package .+ Warning|Overfull|Underfull|undefined references|undefined citations|"
    r"Please.*(?:rerun|Biber)|(?:^|\s)WARN(?:ING)?\s+-\s|^Warning--",
    re.I,
)
POSITION = re.compile(r"^\s*(.+?\.(?:tex|sty|cls|bib|bbl|bcf)):(\d+):\s*(.*)", re.I)
INPUT_LINES = re.compile(r"(?:input line|at lines?)\s+(\d+)(?:--?(\d+))?", re.I)
TEX_TRACE = re.compile(r"^\s*l\.(\d+)\b")


def parse_log(text, stream="output.log"):
    diagnostics = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        position = POSITION.match(line)
        error = ERROR.search(line) or (
            position
            and re.search(
                r"\berror\b|Undefined control sequence|Missing .+ inserted", position[3], re.I
            )
        )
        if not error and not WARNING.search(line):
            continue

        input_line = INPUT_LINES.search(line)
        source_file = position[1] if position else None
        source_line = int(position[2]) if position else int(input_line[1]) if input_line else None
        source_end = (
            int(input_line[2]) if input_line and input_line[2] and not position else source_line
        )
        end = index
        if line.lstrip().startswith("!") and source_line is None:
            for near in range(index + 1, min(index + 8, len(lines))):
                following = lines[near]
                if (
                    ERROR.search(following)
                    or WARNING.search(following)
                    or POSITION.match(following)
                ):
                    break
                if trace := TEX_TRACE.match(following):
                    source_line = source_end = int(trace[1])
                    end = near
                    break
        diagnostics.append(
            {
                "severity": "error" if error else "warning",
                "stream": stream,
                "log_line": index + 1,
                "log_end_line": end + 1,
                "message": line[:2000],
                "excerpt": "\n".join(value[:500] for value in lines[index : end + 1]),
                "source_file": source_file,
                "source_line": source_line,
                "source_end_line": source_end,
                "source_location_status": "reported_file_line"
                if source_file
                else "reported_line_only"
                if source_line is not None
                else "unavailable",
                "source_path_trust": "reported_by_compiler_not_a_local_file_instruction",
            }
        )
    return diagnostics


def classify(response, log=None, stderr=None, blg=None):
    diagnostics = (
        parse_log(log or "")
        + parse_log(stderr or "", "output.stderr")
        + parse_log(blg or "", "output.blg")
    )
    raw = str(response.get("status", "unknown")).lower()
    stats = response.get("stats")
    count = stats.get("latexmk-errors") if isinstance(stats, dict) else None
    outputs = response.get("outputFiles")
    outputs = outputs if isinstance(outputs, list) else []
    failure = (
        raw in ("failure", "failed", "error", "timeout", "timedout", "compile-error")
        or (type(count) in (int, float) and count > 0)
        or any(d["severity"] == "error" for d in diagnostics)
    )
    if failure:
        status = "failed"
    elif raw != "success" or not log:
        status = "unknown"
    elif any(d["severity"] == "warning" for d in diagnostics):
        status = "warnings"
    elif not any(isinstance(f, dict) and f.get("path") == "output.pdf" for f in outputs):
        status = "unknown"
    else:
        status = "clean"
    return status, diagnostics
