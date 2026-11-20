"""Shared fixtures for pdf-mcp tests. All PDFs generated with PyMuPDF — no external files."""

from pathlib import Path

import pymupdf
import pytest


@pytest.fixture
def text_pdf(tmp_path: Path) -> str:
    """3-page PDF with a 3-entry TOC and known text per page."""
    doc = pymupdf.open()
    bodies = [
        "We introduce the method.",
        "The experiments show strong results.",
        "We conclude the paper.",
    ]
    titles = ["Introduction", "Experiments", "Conclusion"]
    for title, body in zip(titles, bodies):
        page = doc.new_page()
        page.insert_text((72, 72), title, fontsize=18)
        page.insert_text((72, 120), body, fontsize=12)
    doc.set_toc(
        [
            [1, "Introduction", 1],
            [1, "Experiments", 2],
            [1, "Conclusion", 3],
        ]
    )
    out = tmp_path / "text.pdf"
    doc.save(out)
    doc.close()
    return str(out)


@pytest.fixture
def table_pdf(tmp_path: Path) -> str:
    """1-page PDF with a 3-col x 4-row ruled table, all 12 cells labeled."""
    doc = pymupdf.open()
    page = doc.new_page()
    xs = [100, 200, 300, 400]
    ys = [100, 140, 180, 220, 260]
    for x in xs:
        page.draw_line(pymupdf.Point(x, ys[0]), pymupdf.Point(x, ys[-1]))
    for y in ys:
        page.draw_line(pymupdf.Point(xs[0], y), pymupdf.Point(xs[-1], y))
    labels = ["A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3", "A4", "B4", "C4"]
    i = 0
    for row in range(4):
        for col in range(3):
            page.insert_text((xs[col] + 5, ys[row + 1] - 12), labels[i])
            i += 1
    out = tmp_path / "table.pdf"
    doc.save(out)
    doc.close()
    return str(out)


@pytest.fixture
def multi_table_pdf(tmp_path: Path) -> str:
    """2-page PDF, each page with one ruled 3-col x 4-row table (same shape as
    `table_pdf`). Used to exercise real truncation (len > max_tables)."""
    doc = pymupdf.open()
    for _ in range(2):
        page = doc.new_page()
        xs = [100, 200, 300, 400]
        ys = [100, 140, 180, 220, 260]
        for x in xs:
            page.draw_line(pymupdf.Point(x, ys[0]), pymupdf.Point(x, ys[-1]))
        for y in ys:
            page.draw_line(pymupdf.Point(xs[0], y), pymupdf.Point(xs[-1], y))
        labels = ["A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3", "A4", "B4", "C4"]
        i = 0
        for row in range(4):
            for col in range(3):
                page.insert_text((xs[col] + 5, ys[row + 1] - 12), labels[i])
                i += 1
    out = tmp_path / "multi_table.pdf"
    doc.save(out)
    doc.close()
    return str(out)


@pytest.fixture
def multi_section_pdf(tmp_path: Path) -> str:
    """6-page PDF with nested TOC; page text chosen so AND/OR/section tests are meaningful.

    Page text (1-indexed):
      p1 "alpha beta intro"   p2 "alpha method"   p3 "beta metric"
      p4 "alpha beta results" p5 "gamma note"     p6 "delta note"
    """
    doc = pymupdf.open()
    bodies = [
        "alpha beta intro",
        "alpha method",
        "beta metric",
        "alpha beta results",
        "gamma note",
        "delta note",
    ]
    for body in bodies:
        page = doc.new_page()
        page.insert_text((72, 72), "body", fontsize=12)
        page.insert_text((72, 110), body, fontsize=12)
    doc.set_toc(
        [
            [1, "Methods", 1],
            [2, "Alpha", 2],
            [2, "Beta", 3],
            [1, "Results", 4],
            [2, "Alpha Results", 4],
            [2, "Beta Ablation", 5],
            [1, "Discussion", 6],
        ]
    )
    out = tmp_path / "multi.pdf"
    doc.save(out)
    doc.close()
    return str(out)
