import gzip
import io
import tarfile

import httpx
import pytest

from tex_mcp.acquire import Acquisition, arxiv_ref
from tex_mcp.document import parse_document
from tex_mcp.models import Limits, TexError
from tex_mcp.syntax import locations


def project(tmp_path, body, preamble=""):
    (tmp_path / "main.tex").write_text(
        "\\documentclass{article}\n"
        + preamble
        + "\n\\begin{document}\n"
        + body
        + "\n\\end{document}"
    )
    return tmp_path


def test_locations_clip_literal_but_keep_macro_invocation():
    segments = [
        {
            "start": 0,
            "end": 6,
            "expanded": False,
            "uncertain": False,
            "origin": {"file": "main.tex", "start": 10, "end": 16, "line": 5, "end_line": 6},
        },
        {
            "start": 6,
            "end": 10,
            "expanded": True,
            "uncertain": False,
            "origin": {"file": "extra.tex", "start": 1, "end": 12, "line": 2, "end_line": 2},
        },
    ]
    literal, macro = locations(segments, 3, 8, text="AB\nCDEWXYZ")
    assert (literal["start"], literal["end"], literal["line"], literal["end_line"]) == (
        13,
        16,
        6,
        6,
    )
    assert (macro["start"], macro["end"], macro["expanded"]) == (1, 12, True)


def test_section_reference_resolves_later_cross_file_figure(tmp_path):
    project(
        tmp_path,
        r"""\section{Intro}Start
\section{Background}Background
\section{Method}\subsection{One}A\subsection{Two}B
\subsection{Three}See \figref{fig:architecture} and \eqref{eq:one}.
\input{objects}""",
        r"\newcommand{\figref}[1]{Figure~\ref{#1}}",
    )
    (tmp_path / "objects.tex").write_text(r"""\begin{figure}\includegraphics{diagram.pdf}
\caption{Architecture}\label{fig:architecture}\end{figure}
\begin{equation}x=1\label{eq:one}\end{equation}""")
    (tmp_path / "diagram.pdf").write_bytes(b"placeholder")
    doc = parse_document(tmp_path)
    section = next(s for s in doc["sections"] if s["id"] == "3.3")
    refs = [
        e
        for e in doc["edges"]
        if section["start"] <= e["start"] < section["end"] and e["kind"] == "object_reference"
    ]
    assert {r["target"] for r in refs} == {"figure:1", "equation:1"}
    figure = next(o for o in doc["objects"] if o["kind"] == "figure")
    assert figure["caption"] == "Architecture"
    assert figure["assets"][0]["paths"] == ["diagram.pdf"]
    assert figure["source_locations"][0]["file"] == "objects.tex"


def test_macro_order_and_group_scope(tmp_path):
    project(
        tmp_path,
        r"""\section{One}\newcommand{\word}{FIRST}
BEFORE \word {\renewcommand{\word}{LOCAL}INNER \word} OUTER \word
\renewcommand{\word}{SECOND} AFTER \word""",
    )
    text = parse_document(tmp_path)["text"]
    assert "BEFORE FIRST" in text and "INNER LOCAL" in text
    assert "OUTER FIRST" in text and "AFTER SECOND" in text


def test_macro_expands_inside_caption_and_math(tmp_path):
    project(
        tmp_path,
        r"\section{One}\begin{figure}\caption{A \word}\end{figure}$\word$",
        r"\newcommand{\word}{TOKEN}",
    )
    doc = parse_document(tmp_path)
    assert doc["objects"][0]["caption"] == "A TOKEN"
    assert "$TOKEN$" in doc["text"]


def test_repeated_input_is_not_cycle_and_actual_cycle_reported(tmp_path):
    project(tmp_path, r"\section{One}\input{part}\input{part}")
    (tmp_path / "part.tex").write_text("FRAGMENT")
    assert parse_document(tmp_path)["text"].count("FRAGMENT") == 2
    (tmp_path / "part.tex").write_text(r"\input{main}")
    assert any(d["code"] == "INPUT_CYCLE" for d in parse_document(tmp_path)["diagnostics"])


def test_false_branch_and_verbatim_preserved(tmp_path):
    project(
        tmp_path,
        r"""\section{Visible}\iffalse\section{Hidden}HIDDEN\else SHOWN\fi
\begin{verbatim}
100% literal text \ref{not-a-real-ref}
\end{verbatim}""",
    )
    doc = parse_document(tmp_path)
    assert [s["title"] for s in doc["sections"]] == ["Visible"]
    assert "100% literal text" in doc["text"]
    assert not doc["edges"]


def test_unknown_condition_not_claimed_complete(tmp_path):
    project(tmp_path, r"\section{One}\iffoo YES\else NO\fi")
    assert any(d["code"] == "UNKNOWN_CONDITION" for d in parse_document(tmp_path)["diagnostics"])


def test_bbl_fills_missing_bib_and_bib_keeps_identifiers(tmp_path):
    project(tmp_path, r"\section{One}\cite{bibkey,bblkey,missing}\bibliography{refs}")
    (tmp_path / "refs.bib").write_text(
        '@string{venue="Example"}\n@article{bibkey,title={A {Nested} Title},author={John Smith and Jane Smith},year={2020},journal=venue,doi={10.1234/example}}'
    )
    (tmp_path / "main.bbl").write_text(
        r"\begin{thebibliography}{1}\bibitem{bblkey}Rendered Reference\end{thebibliography}"
    )
    doc = parse_document(tmp_path)
    refs = doc["references"]
    assert refs["bblkey"]["source"]["format"] == "bbl"
    assert refs["missing"]["status"] == "missing"
    assert refs["bibkey"]["identifiers_from_source"] == ["doi:10.1234/example"]
    assert len(refs["bibkey"]["authors"]) == 2
    assert refs["bibkey"]["fields"]["journal"] == "Example"
    assert refs["bibkey"]["cited_at"][0]["section_id"] == "1"


def test_main_ambiguity_and_path_escape(tmp_path):
    project(tmp_path, r"\section{One}Text")
    (tmp_path / "supp.tex").write_text((tmp_path / "main.tex").read_text())
    with pytest.raises(TexError) as error:
        parse_document(tmp_path)
    assert error.value.code == "MAIN_AMBIGUOUS"
    assert parse_document(tmp_path, "supp.tex")["main_tex"] == "supp.tex"
    with pytest.raises(TexError):
        parse_document(tmp_path, "../other.tex")


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "escape"])
def test_archive_rejects_links_and_traversal(tmp_path, kind):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        member = tarfile.TarInfo("../escape" if kind == "escape" else "link")
        if kind == "symlink":
            member.type = tarfile.SYMTYPE
            member.linkname = "../outside"
        elif kind == "hardlink":
            member.type = tarfile.LNKTYPE
            member.linkname = "../outside"
        archive.addfile(member)
    with pytest.raises(TexError):
        Acquisition(interval=0).unpack(buffer.getvalue(), tmp_path)
    assert not (tmp_path.parent / "escape").exists()


def test_single_gzip_and_html_validation(tmp_path):
    payload = gzip.compress(b"\\documentclass{article}\\begin{document}Hello\\end{document}")
    Acquisition(interval=0).unpack(payload, tmp_path)
    assert (tmp_path / "main.tex").exists()
    with pytest.raises(TexError):
        Acquisition(interval=0).unpack(b"<html>blocked</html>", tmp_path)


def test_source_size_budget(tmp_path):
    with pytest.raises(TexError) as error:
        Acquisition(Limits(max_source_bytes=10), interval=0).unpack(b"X" * 100, tmp_path)
    assert error.value.code == "BUDGET"


@pytest.mark.parametrize(
    "source,expected",
    [
        ("arxiv:1706.03762v2", ("1706.03762", "v2")),
        ("https://arxiv.org/pdf/1706.03762v2.pdf?download=1", ("1706.03762", "v2")),
        ("hep-th/9901001", ("hep-th/9901001", None)),
    ],
)
def test_source_refs(source, expected):
    assert arxiv_ref(source) == expected


def test_simple_def_and_optional_macro_arguments(tmp_path):
    project(
        tmp_path,
        r"\section{One}\def\word#1{TOKEN#1}\newcommand{\opt}[2][DEFAULT]{#1+#2}\word{X}\opt{Y}\opt[OTHER]{Z}",
    )
    text = parse_document(tmp_path)["text"]
    assert "TOKENX" in text and "DEFAULT+Y" in text and "OTHER+Z" in text


def test_parent_relative_include_inside_root_is_allowed(tmp_path):
    project(tmp_path, r"\section{One}\input{sections/part}")
    (tmp_path / "sections").mkdir()
    (tmp_path / "sections/part.tex").write_text(r"\input{../fragment}")
    (tmp_path / "fragment.tex").write_text("INNER_ROOT")
    assert "INNER_ROOT" in parse_document(tmp_path)["text"]


def test_duplicate_labels_and_unresolved_refs_are_reported(tmp_path):
    project(
        tmp_path,
        r"\section{One}\ref{missing}\begin{equation}x\label{duplicate}\end{equation}\begin{equation}y\label{duplicate}\end{equation}\ref{duplicate}",
    )
    doc = parse_document(tmp_path)
    assert any(d["code"] == "DUPLICATE_LABEL" for d in doc["diagnostics"])
    assert {e["status"] for e in doc["edges"]} == {"ambiguous", "unresolved"}


def test_macro_recursion_and_output_size_have_bounds(tmp_path):
    project(tmp_path, r"\section{One}\newcommand{\foo}{\foo}\foo")
    assert any(d["code"] == "UNEXPANDED_MACRO" for d in parse_document(tmp_path)["diagnostics"])
    project(tmp_path, r"\section{One}" + ("X" * 3000))
    with pytest.raises(TexError) as e:
        parse_document(tmp_path, max_chars=1000)
    assert e.value.code == "PARSE_BUDGET"


def test_bbl_identifiers_are_lookup_claims(tmp_path):
    project(tmp_path, r"\section{One}\cite{a,b}")
    (tmp_path / "main.bbl").write_text(
        r"\bibitem{a}\url{https://doi.org/10.1234/a}\bibitem{b}arXiv:1706.03762v2"
    )
    refs = parse_document(tmp_path)["references"]
    assert refs["a"]["identifiers_from_source"] == ["doi:10.1234/a"]
    assert refs["b"]["identifiers_from_source"] == ["arxiv:1706.03762v2"]
    assert refs["a"]["external_identity"] == "unverified"


def test_nocite_inclusion_is_distinct_from_in_text_citation(tmp_path):
    project(tmp_path, r"\section{One}\nocite{*}")
    (tmp_path / "refs.bib").write_text("@article{a,title={One},year={2020}}")
    record = parse_document(tmp_path)["references"]["a"]
    assert record["included_by_nocite"] and not record["cited_in_body"]


def test_starred_reference_and_missing_graphic_report(tmp_path):
    project(
        tmp_path,
        r"\section{One}\ref*{fig:x}\begin{figure}\includegraphics{absent}\label{fig:x}\end{figure}",
    )
    doc = parse_document(tmp_path)
    assert doc["edges"][0]["target"] == "figure:1"
    assert doc["objects"][0]["assets"][0]["status"] == "missing"


def test_file_symlink_and_bibliography_escape_rejected(tmp_path):
    project(tmp_path, r"\section{One}\bibliography{../outside}")
    with pytest.raises(TexError):
        parse_document(tmp_path)


def test_network_download_budget_and_error_classification(tmp_path):
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"X" * 100))
    )
    with pytest.raises(TexError) as e:
        Acquisition(Limits(max_download_bytes=10), client, 0).get("https://example.org")
    assert e.value.code == "BUDGET"
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(403)))
    with pytest.raises(TexError) as e:
        Acquisition(client=client, interval=0).get("https://example.org")
    assert e.value.details["status_code"] == 403


def test_captionof_bounded_figure_and_display_equation_labels(tmp_path):
    project(
        tmp_path,
        r"\section{One}\ref{fig:teaser}\eqref{eq:display}\begin{center}\includegraphics{image.png}\captionof{figure}{Teaser}\label{fig:teaser}\end{center}\[x=1\label{eq:display}\]",
    )
    (tmp_path / "image.png").write_bytes(b"placeholder")
    doc = parse_document(tmp_path)
    assert {e["target"] for e in doc["edges"]} == {"figure:1", "equation:1"}
    assert doc["objects"][0]["caption"] == "Teaser"
