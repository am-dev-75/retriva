# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

"""Tests for the PDF parser and PdfPlumberExtractor."""

import re
from pathlib import Path

import pytest
from fpdf import FPDF

from retriva.ingestion.pdf_parser import (
    PdfPage,
    PdfDocument,
    PdfPlumberExtractor,
    parse_pdf,
    derive_title,
)


# ---------------------------------------------------------------------------
# Fixtures: programmatic PDF generation
# ---------------------------------------------------------------------------

def _create_pdf(pages_text: list[str], path: Path, title: str = "") -> Path:
    """Create a minimal PDF with the given page texts using fpdf2."""
    pdf = FPDF()
    if title:
        pdf.set_title(title)
    pdf.set_auto_page_break(auto=False)
    for text in pages_text:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        # Write each line
        for line in text.split("\n"):
            pdf.cell(0, 10, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))
    return path


@pytest.fixture
def sample_pdf(tmp_path):
    """A 3-page PDF with extractable text."""
    return _create_pdf(
        [
            "Board X Manual\nRevision 2.1\nApril 2026",
            "Chapter 1: Installation\nConnect the power supply to the main board.\nEnsure all LEDs are green.",
            "Chapter 2: Diagnostics\nRun the startup test sequence.\nCheck fan speed readings.",
        ],
        tmp_path / "board_x_manual.pdf",
        title="Board X Operations Manual",
    )


@pytest.fixture
def empty_page_pdf(tmp_path):
    """A PDF where page 2 has no text (just whitespace)."""
    return _create_pdf(
        [
            "Page with content",
            "   ",  # Will produce empty/whitespace text
            "More content here",
        ],
        tmp_path / "empty_page.pdf",
    )


@pytest.fixture
def no_title_pdf(tmp_path):
    """A PDF with no metadata title."""
    return _create_pdf(
        ["Some generic content without a heading-like first line that would match."],
        tmp_path / "technical_notes.pdf",
        title="",
    )


# ---------------------------------------------------------------------------
# Tests: PdfPlumberExtractor
# ---------------------------------------------------------------------------

class TestPdfPlumberExtractor:
    def test_extract_pages_returns_all_pages(self, sample_pdf):
        extractor = PdfPlumberExtractor()
        pages = extractor.extract_pages(sample_pdf)
        assert pages is not None
        assert len(pages) == 3
        assert pages[0]["page_number"] == 1
        assert pages[1]["page_number"] == 2
        assert pages[2]["page_number"] == 3

    def test_extract_pages_text_content(self, sample_pdf):
        extractor = PdfPlumberExtractor()
        pages = extractor.extract_pages(sample_pdf)
        assert "Board X Manual" in pages[0]["text"]
        assert "Installation" in pages[1]["text"]
        assert "Diagnostics" in pages[2]["text"]

    def test_extract_metadata(self, sample_pdf):
        extractor = PdfPlumberExtractor()
        metadata = extractor.extract_metadata(sample_pdf)
        assert isinstance(metadata, dict)
        # fpdf2 sets the title in metadata
        assert "Title" in metadata or "title" in metadata or len(metadata) > 0

    def test_nonexistent_file_returns_none(self, tmp_path):
        extractor = PdfPlumberExtractor()
        result = extractor.extract_pages(tmp_path / "missing.pdf")
        assert result is None

    def test_nonexistent_file_metadata_empty(self, tmp_path):
        extractor = PdfPlumberExtractor()
        result = extractor.extract_metadata(tmp_path / "missing.pdf")
        assert result == {}

    def test_corrupt_file_returns_none(self, tmp_path):
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_text("This is not a PDF file at all.")
        extractor = PdfPlumberExtractor()
        result = extractor.extract_pages(corrupt)
        assert result is None


# ---------------------------------------------------------------------------
# Tests: parse_pdf
# ---------------------------------------------------------------------------

class TestParsePdf:
    def test_parses_all_pages(self, sample_pdf):
        doc = parse_pdf(sample_pdf)
        assert doc is not None
        assert isinstance(doc, PdfDocument)
        assert len(doc.pages) == 3
        assert doc.total_pages == 3
        assert doc.skipped_pages == 0

    def test_page_numbers_are_1_indexed(self, sample_pdf):
        doc = parse_pdf(sample_pdf)
        for i, page in enumerate(doc.pages):
            assert page.page_number == i + 1

    def test_source_path_is_absolute(self, sample_pdf):
        doc = parse_pdf(sample_pdf)
        assert Path(doc.source_path).is_absolute()

    def test_title_from_metadata(self, sample_pdf):
        doc = parse_pdf(sample_pdf)
        # The PDF was created with title="Board X Operations Manual"
        assert "Board X" in doc.title or "board_x" in doc.title.lower()

    def test_nonexistent_returns_none(self, tmp_path):
        result = parse_pdf(tmp_path / "nope.pdf")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: derive_title
# ---------------------------------------------------------------------------

class TestDeriveTitle:
    def test_metadata_title_preferred(self):
        title = derive_title(
            {"Title": "Operations Manual v3"},
            "Some page text",
            Path("/data/doc.pdf"),
        )
        assert title == "Operations Manual v3"

    def test_heading_from_first_page(self):
        title = derive_title(
            {},
            "Board X Installation Guide\nSome body text follows here.",
            Path("/data/doc.pdf"),
        )
        assert title == "Board X Installation Guide"

    def test_filename_fallback(self):
        title = derive_title({}, "", Path("/data/technical_notes.pdf"))
        assert "Technical Notes" in title

    def test_filename_with_underscores(self):
        title = derive_title({}, "", Path("/data/fan_curve_notes.pdf"))
        assert "Fan Curve Notes" in title

    def test_ignores_path_like_title(self):
        """PDF metadata sometimes contains file paths instead of real titles."""
        title = derive_title(
            {"Title": "/usr/share/doc/manual.pdf"},
            "Real First Heading Here",
            Path("/data/manual.pdf"),
        )
        # Should NOT use the path-like metadata title
        assert title != "/usr/share/doc/manual.pdf"

    def test_ignores_very_short_title(self):
        title = derive_title(
            {"Title": "ab"},
            "Proper Document Title Here",
            Path("/data/doc.pdf"),
        )
        assert title == "Proper Document Title Here"
