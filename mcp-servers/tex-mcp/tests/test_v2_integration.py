import io
import json
import tarfile
from pathlib import Path

import httpx
import pymupdf
import pytest

from tex_mcp import images
from tex_mcp.models import TexError
from tex_mcp.service import Service


def write_project(root):
    root.mkdir()
    (root / "main.tex").write_text(r"""\documentclass{article}
\newcommand{\figref}[1]{Figure~\ref{#1}}
\begin{document}\section{Intro}Start\section{Background}Background
\section{Method}\subsection{One}One\subsection{Two}Two
\subsection{Three}See \figref{fig:arch} twice \ref{fig:arch} and \eqref{eq:x}. \cite{needed}
\section{Elsewhere}\input{objects}\bibliography{refs}\end{document}""")
    (
        root / "objects.tex"
    ).write_text(r"""\begin{figure}\includegraphics{picture.pdf}\caption{Architecture}\label{fig:arch}\end{figure}
\begin{equation}x=1\label{eq:x}\end{equation}""")
    (root / "refs.bib").write_text(
        "@article{needed,title={An Article},author={A Author},year={2020},doi={10.1234/article}}"
    )
    pdf = pymupdf.open()
    pdf.new_page(width=100, height=100)
    pdf.save(root / "picture.pdf")
    pdf.close()
    return root


def all_pages(s, doc, **kwargs):
    items = []
    cursor = None
    while True:
        result = s.read(doc, cursor=cursor, **kwargs)
        assert len(json.dumps(result, ensure_ascii=False)) <= kwargs.get("max_chars", 24000)
        items += result["items"]
        cursor = result["next_cursor"]
        if not cursor:
            return items


def test_user_section_33_returns_outside_picture_and_equation(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    items = all_pages(s, doc, section="3.3")
    objects = [i for i in items if i["kind"] == "object"]
    assert {i["object_id"] for i in objects} == {"figure:1", "equation:1"}
    figure = next(i for i in objects if i["object_id"] == "figure:1")
    assert figure["relationship"] == "directly_referenced"
    assert figure["defined_in_section"] == "4" and figure["caption"] == "Architecture"
    assert Path(figure["assets"][0]["image_path"]).exists()
    assert len(figure["referenced_at"]) == 2
    assert next(i for i in items if i["kind"] == "reference")["key"] == "needed"


def test_read_body_provenance_and_local_citations_without_external_objects(tmp_path):
    source = write_project(tmp_path / "source")
    main = source / "main.tex"
    main.write_text(main.read_text().replace(r"\cite{needed}", r"\input{passage.tex}"))
    (source / "passage.tex").write_text("Evidence from a second file.\n" + r"\cite{needed,absent}")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    items = all_pages(s, doc, section="3.3", include_referenced=False)
    assert not any(item["kind"] == "object" for item in items)
    assert {item["key"]: item["status"] for item in items if item["kind"] == "reference"} == {
        "needed": "parsed",
        "absent": "missing",
    }
    body = [item for item in items if item["kind"] == "body"]
    origins = [loc for item in body for loc in item["source_locations"]]
    assert {loc["file"] for loc in origins} == {"main.tex", "passage.tex"}
    assert any(loc["file"] == "main.tex" and loc["expanded"] for loc in origins)
    assert any(loc["file"] == "passage.tex" and loc["line"] == 1 for loc in origins)


def test_compare_detects_replaced_figure_data(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    first = s.open(str(source))["document_id"]
    with pymupdf.open() as pdf:
        pdf.new_page(width=140, height=100)
        pdf.save(source / "picture.pdf")
    second = s.open(str(source))["document_id"]
    items = s.compare(first, second)["items"]
    assert len(items) == 1
    difference = items[0]
    assert difference["key"] == "fig:arch"
    assert difference["changed_fields"] == ["assets"]
    old, new = (difference[side] for side in ("left", "right"))
    assert old["source_locations"][0]["file"] == new["source_locations"][0]["file"] == "objects.tex"
    assert old["assets"][0]["files"][0]["sha256"] != new["assets"][0]["files"][0]["sha256"]


def test_compare_matches_reordered_labels_and_reports_ambiguous_titles(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    main = source / "main.tex"
    a = r"\section{First}\label{sec:first} First passage."
    b = r"\section{Second}\label{sec:second} Second passage."
    repeated = r"\section{Repeat}A\section{Repeat}B"

    def write(body):
        main.write_text(r"\documentclass{article}\begin{document}" + body + r"\end{document}")

    s = Service(tmp_path / "cache", interval=0)
    write(a + b + repeated)
    first = s.open(str(source))["document_id"]
    write(b + a + repeated)
    second = s.open(str(source))["document_id"]
    changes = {d["key"]: d for d in s.compare(first, second)["items"]}
    assert changes["sec:first"]["status"] == changes["sec:second"]["status"] == "moved"
    assert changes["sec:first"]["match_basis"] == "label"
    assert changes["Repeat"]["status"] == "ambiguous"


def test_match_read_returns_only_local_evidence_across_pages(tmp_path):
    source = write_project(tmp_path / "source")
    main = source / "main.tex"
    main.write_text(
        main.read_text().replace(
            r"\subsection{Three}See",
            r"\subsection{Three} Unrelated \cite{excluded} " + " filler" * 100 + " See",
        )
    )
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    match = s.search(doc, "See", section="3.3")["matches"][0]
    args = {
        "match_ref": match["match_ref"],
        "context_chars": 120,
        "max_chars": 2000,
        "asset_mode": "metadata",
    }
    first = s.read(doc, **args)
    assert first["truncated"]
    assert first["items"][0]["match_range"] == [match["start"], match["end"]]
    items, fragments = [], {}
    for record in all_pages(s, doc, **args):
        if record["kind"] != "record_fragment":
            items.append(record)
            continue
        parts = fragments.setdefault(record["record_index"], [])
        assert record["part"] == len(parts)
        parts.append(record["text"])
        if record["final"]:
            items.append(json.loads("".join(parts)))
            del fragments[record["record_index"]]
    assert not fragments
    body = "".join(record["text"] for record in items if record["kind"] == "body")
    assert "See" in body and "Unrelated" not in body
    assert {item["object_id"] for item in items if item["kind"] == "object"} == {
        "figure:1",
        "equation:1",
    }
    assert {item["key"] for item in items if item["kind"] == "reference"} == {"needed"}

    with pytest.raises(TexError) as bad_cursor:
        s.read(doc, cursor=first["next_cursor"], **{**args, "context_chars": 90})
    assert bad_cursor.value.code == "INVALID_CURSOR"
    main.write_text(main.read_text().replace("Unrelated", "Revised"))
    revised = s.open(str(source))["document_id"]
    with pytest.raises(TexError) as wrong_snapshot:
        s.read(revised, **args)
    assert wrong_snapshot.value.code == "INVALID_MATCH_REF"


def test_match_context_clips_to_search_scope_and_source_view(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    match = s.search(doc, "Two", section="3.2")["matches"][-1]
    exact = s.read(doc, match_ref=match["match_ref"], context_chars=0, view="source")
    assert [r["text"] for r in exact["items"] if r["kind"] == "source_fragment"] == ["Two"]
    wide = s.read(doc, match_ref=match["match_ref"], context_chars=4000)
    body = "".join(r["text"] for r in wide["items"] if r["kind"] == "body")
    assert "Two" in body and "Three" not in body
    for args, code in [
        ({"match_ref": "garbled"}, "INVALID_MATCH_REF"),
        ({"match_ref": match["match_ref"], "section": "3.2"}, "INVALID_INPUT"),
        ({"match_ref": match["match_ref"], "context_chars": 4001}, "INVALID_INPUT"),
        ({"context_chars": 10}, "INVALID_INPUT"),
    ]:
        with pytest.raises(TexError) as invalid:
            s.read(doc, **args)
        assert invalid.value.code == code


def test_match_inside_figure_preserves_text_and_returns_attachment(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    match = s.search(doc, "Architecture")["matches"][0]
    items = all_pages(s, doc, match_ref=match["match_ref"], context_chars=0, asset_mode="metadata")
    assert any(item.get("text") == "Architecture" for item in items)
    assert any(item.get("object_id") == "figure:1" for item in items)


def test_regex_match_preview_and_local_read_are_bounded(tmp_path):
    source = write_project(tmp_path / "source")
    main = source / "main.tex"
    main.write_text(main.read_text().replace("Start", "Z" * 9000))
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    match = s.search(doc, "Z+", mode="regex")["matches"][0]
    assert match["end"] - match["start"] == 9000
    assert len(match["snippet"]) <= 500
    with pytest.raises(TexError) as wide:
        s.read(doc, match_ref=match["match_ref"])
    assert wide.value.code == "MATCH_TOO_WIDE"


def test_snapshot_changes_by_content_not_maximum_mtime(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    first = s.open(str(source))["document_id"]
    old = s.storage.get(first)
    (source / "main.tex").write_text((source / "main.tex").read_text().replace("See", "Changed"))
    second = s.open(str(source))["document_id"]
    assert first != second and s.storage.get(first) == old
    assert s.document(first)["text"] != s.document(second)["text"]
    restarted = Service(tmp_path / "cache", interval=0)
    assert restarted.document(first)["text"] == old["text"]


def test_whole_read_once_and_no_section_body_survives(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.tex").write_text(
        r"\documentclass{article}\begin{document}\section{A}A\subsection{B}UNIQUE\end{document}"
    )
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    content = "".join(i["text"] for i in all_pages(s, doc) if i["kind"] == "body")
    assert content.count("UNIQUE") == 1
    (source / "main.tex").write_text(
        r"\documentclass{article}\begin{document}PLAIN_BODY\end{document}"
    )
    doc = s.open(str(source))["document_id"]
    assert "PLAIN_BODY" in "".join(i["text"] for i in all_pages(s, doc) if i["kind"] == "body")


def test_output_budget_continues_body_and_large_table(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.tex").write_text(
        r"\documentclass{article}\begin{document}\section{A}"
        + ("TEXT " * 3000)
        + r"\begin{table}\caption{Large}"
        + ("CELL " * 3000)
        + r"\end{table}\end{document}"
    )
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    items = all_pages(s, doc, max_chars=2200)
    assert "".join(i["text"] for i in items if i["kind"] == "body").count("TEXT") == 3000
    fragments = [i for i in items if i["kind"] == "record_fragment"]
    assert fragments and fragments[-1]["final"]
    obj = json.loads("".join(i["text"] for i in fragments))
    assert obj["latex"].count("CELL") == 3000


def test_cache_modified_is_rejected_and_source_file_is_original(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    original = s.read_file(doc, "objects.tex")["items"][0]["text"]
    assert r"\includegraphics{picture.pdf}" in original
    (s.storage.source_root(doc) / "main.tex").write_text("tampered")
    with pytest.raises(TexError) as exc:
        s.outline(doc)
    assert exc.value.code == "CACHE_CHANGED"


def test_reference_handoff_does_not_invent_identity(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    result = s.reference_lookups(doc)
    assert result["items"][1]["paper_search_inputs"] == [{"identifier": "doi:10.1234/article"}]
    assert result["items"][1]["external_identity"] == "unverified"


def test_dpi_cache_and_explicit_original_pdf_crop(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    data = s.document(doc)
    obj = s.object(data, "fig:arch")
    one = s.object_payload(data, obj, "images", 36)["assets"][0]["image_path"]
    two = s.object_payload(data, obj, "images", 300)["assets"][0]["image_path"]
    assert one != two and pymupdf.Pixmap(one).width == 50 and pymupdf.Pixmap(two).width == 417
    attachment = images.attach_pdf(s.storage, doc, source / "picture.pdf")
    image = images.render_object(
        s.storage, doc, obj, pdf_ref=attachment["pdf_ref"], page=1, bbox=[0, 0, 50, 50], dpi=72
    )
    assert pymupdf.Pixmap(image["image_path"]).width == 50
    assert image["pdf_identity_status"] == "unverified"
    Path(one).write_bytes(b"broken PNG")
    recovered = s.object_payload(data, obj, "images", 36)["assets"][0]
    assert recovered["image_status"] == "ready"
    assert pymupdf.Pixmap(recovered["image_path"]).width == 50
    Path(image["image_path"]).write_bytes(b"broken crop")
    recovered_crop = images.render_object(
        s.storage, doc, obj, pdf_ref=attachment["pdf_ref"], page=1, bbox=[0, 0, 50, 50], dpi=72
    )
    assert pymupdf.Pixmap(recovered_crop["image_path"]).width == 50


def test_version_pinned_before_download_and_no_cache_collision(tmp_path):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if "/api/query" in request.url.path:
            requested = request.url.params["id_list"]
            v = "v1" if requested.endswith("v1") else "v2"
            return httpx.Response(
                200,
                text='<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1706.03762'
                + v
                + "</id></entry></feed>",
            )
        version = "ONE" if str(request.url).endswith("v1") else "TWO"
        data = ("\\documentclass{article}\\begin{document}" + version + "\\end{document}").encode()
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            entry = tarfile.TarInfo("main.tex")
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
        return httpx.Response(200, content=buffer.getvalue())

    s = Service(
        tmp_path / "cache", httpx.Client(transport=httpx.MockTransport(handler)), interval=0
    )
    one = s.open("1706.03762v1")
    two = s.open("1706.03762v2")
    assert (
        one["document_id"] != two["document_id"]
        and one["actual_version"] == "v1"
        and two["actual_version"] == "v2"
    )
    assert (
        "ONE" in s.document(one["document_id"])["text"]
        and "TWO" in s.document(two["document_id"])["text"]
    )
    previous = len(calls)
    assert s.open("1706.03762v1")["cache_state"] == "hit"
    assert len(calls) == previous
    assert s.open("1706.03762")["document_id"] == two["document_id"]
    assert len(calls) == previous + 1
    assert s.open("1706.03762v1", refresh=True)["document_id"] == one["document_id"]
    assert len(calls) == previous + 3


def test_attach_corrupt_pdf_returns_structured_error(tmp_path):
    source = write_project(tmp_path / "source")
    service = Service(tmp_path / "cache", interval=0)
    document_id = service.open(str(source))["document_id"]
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"not a PDF")
    with pytest.raises(TexError) as error:
        images.attach_pdf(service.storage, document_id, corrupt)
    assert error.value.code == "INVALID_PDF"


def test_isolated_render_rejects_failed_compile_even_with_pdf(tmp_path, monkeypatch):
    from types import SimpleNamespace

    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    obj = s.object(s.document(doc), "fig:arch")
    commands = []
    monkeypatch.setenv("TEX_MCP_RENDER_IMAGE", "example/tex@sha256:" + "a" * 64)
    monkeypatch.setattr(images.shutil, "which", lambda name: "/usr/bin/docker")

    def failed(command, **kwargs):
        commands.append(command)
        bind = next(
            command[i + 1]
            for i, v in enumerate(command)
            if v == "--volume" and command[i + 1].endswith(":/work:rw")
        )
        (Path(bind.removesuffix(":/work:rw")) / "object.pdf").write_bytes(
            (source / "picture.pdf").read_bytes()
        )
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(images.subprocess, "run", failed)
    with pytest.raises(TexError) as e:
        images.render_object(s.storage, doc, obj, method="isolated_tex")
    assert e.value.code == "RENDER_FAILED"
    assert (
        "--network=none" in commands[0]
        and "--read-only" in commands[0]
        and "-no-shell-escape" in commands[0]
    )
    assert "--pull=never" in commands[0]


def test_missing_render_configuration_does_not_run_host_tex(tmp_path, monkeypatch):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    obj = s.object(s.document(doc), "fig:arch")
    monkeypatch.delenv("TEX_MCP_RENDER_IMAGE", raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("No host process should run")

    monkeypatch.setattr(images.subprocess, "run", forbidden)
    with pytest.raises(TexError) as e:
        images.render_object(s.storage, doc, obj, method="isolated_tex")
    assert e.value.code == "RENDER_UNAVAILABLE"


def test_failed_source_import_leaves_no_partial_document(tmp_path):
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, content=b"<html>error</html>")
        )
    )
    s = Service(tmp_path / "cache", client, interval=0)
    with pytest.raises(TexError):
        s.open("1706.03762")
    assert list((s.storage.root / "documents").iterdir()) == []
    assert not list(s.storage.root.glob(".stage-*"))


def test_local_symlink_is_rejected_and_entry_choice_has_distinct_identity(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    first = s.open(str(source))["document_id"]
    (source / "supp.tex").write_text(
        r"\documentclass{article}\begin{document}SUPPLEMENT\end{document}"
    )
    second = s.open(str(source), main_tex="supp.tex")["document_id"]
    assert first != second and "SUPPLEMENT" in s.document(second)["text"]
    (source / "linked.tex").symlink_to(source / "main.tex")
    with pytest.raises(TexError) as e:
        s.open(str(source), main_tex="supp.tex")
    assert e.value.code == "UNSAFE_PATH"


def test_bibliography_unused_entries_not_presented_as_body_citations(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    with (source / "refs.bib").open("a") as stream:
        stream.write("@article{unused,title={Unused},year={2021}}")
    doc = s.open(str(source))["document_id"]
    refs = s.references(doc)["items"]
    assert {r["key"] for r in refs} == {"needed"}
    assert s.storage.get(doc)["references"]["unused"]["cited_in_body"] is False
    assert s.references(doc, keys=["unused"])["items"][0]["key"] == "unused"


def test_section_selector_and_cursor_do_not_silently_guess(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    with pytest.raises(TexError):
        s.read(doc, section="o")
    with pytest.raises(TexError):
        s.read(doc, section="missing")
    first = s.read(doc, max_chars=2200)
    assert first["next_cursor"]
    with pytest.raises(TexError):
        s.read(doc, section="3.3", max_chars=2200, cursor=first["next_cursor"])


def test_read_file_escape_and_invalid_regex_are_structured(tmp_path):
    source = write_project(tmp_path / "source")
    s = Service(tmp_path / "cache", interval=0)
    doc = s.open(str(source))["document_id"]
    with pytest.raises(TexError):
        s.read_file(doc, "../outside.tex")
    with pytest.raises(TexError) as e:
        s.search(doc, "(", mode="regex")
    assert e.value.code == "INVALID_REGEX"


def test_parse_original_representative_fixtures(tmp_path):
    fixtures = Path(__file__).parent / "fixtures"
    s = Service(tmp_path / "cache", interval=0)
    for name in ["single", "multifile", "bibref"]:
        doc = s.open(str(fixtures / name))["document_id"]
        assert s.outline(doc)["outline"]
        assert all_pages(s, doc, asset_mode="metadata")


def test_source_path_is_not_reported_as_a_valid_image(tmp_path):
    source = write_project(tmp_path / "source")
    (source / "picture.pdf").write_text("not a pdf")
    service = Service(tmp_path / "cache", interval=0)
    doc = service.open(str(source))["document_id"]
    obj = service.object(service.document(doc), "fig:arch")
    payload = service.object_payload(service.document(doc), obj, "images")
    assert payload["availability"] == "no_ready_image"
    assert payload["assets"][0]["image_status"] == "rasterization_failed"
