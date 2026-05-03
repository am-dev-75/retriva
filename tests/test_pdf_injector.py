# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
End-to-end fixture test for the PDF injector.

Creates a programmatic PDF and verifies:
- Discovery finds the PDF file
- Pages are parsed with correct text and metadata
- The API endpoint accepts payloads
- CLI --injector pdf flag is advertised
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from fpdf import FPDF

# Ensure default implementations are registered
import retriva.ingestion.chunker  # noqa: F401
import retriva.ingestion.pdf_parser  # noqa: F401 — registers PdfPlumberExtractor


def _create_pdf(pages_text: list[str], path: Path, title: str = "") -> Path:
    """Create a minimal PDF fixture."""
    pdf = FPDF()
    if title:
        pdf.set_title(title)
    pdf.set_auto_page_break(auto=False)
    for text in pages_text:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        for line in text.split("\n"):
            pdf.cell(0, 10, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))
    return path


@pytest.fixture
def pdf_corpus(tmp_path):
    """Create a fake PDF corpus with nested directories."""
    manuals = tmp_path / "manuals"
    manuals.mkdir()
    _create_pdf(
        [
            "Board X Manual\nRevision 2.1",
            "Chapter 1: Installation\nConnect the power supply.",
        ],
        manuals / "board_x_manual.pdf",
        title="Board X Operations Manual",
    )

    diagnostics = tmp_path / "diagnostics"
    diagnostics.mkdir()
    _create_pdf(
        ["Startup LED Sequence\nAll LEDs should be green after 5 seconds."],
        diagnostics / "startup_leds.pdf",
        title="LED Diagnostics",
    )

    # Also add a non-PDF file that should be ignored
    (tmp_path / "notes.txt").write_text("Not a PDF")

    return tmp_path


# ---------------------------------------------------------------------------
# Test: API endpoint
# ---------------------------------------------------------------------------

@patch("retriva.ingestion_api.main.get_client")
@patch("retriva.ingestion_api.main.init_collection")
def test_pdf_endpoint_accepts_payload(mock_init, mock_client):
    """The /api/v1/ingest/pdf endpoint should accept valid payloads."""
    from fastapi.testclient import TestClient
    from retriva.ingestion_api.main import app

    payload = {
        "source_path": "/data/manuals/board_x_manual.pdf",
        "page_title": "Board X Operations Manual",
        "content_text": "Chapter 1: Installation. Connect the power supply.",
        "page_number": 2,
        "total_pages": 3,
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/pdf", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "job_id" in data
    assert "page 2" in data["message"]


# ---------------------------------------------------------------------------
# Test: end-to-end pipeline
# ---------------------------------------------------------------------------

def test_discovery_and_parsing(pdf_corpus):
    """Verify the full discovery → parse → title derivation pipeline."""
    from retriva.ingestion.pdf_parser import parse_pdf

    # 1. Discovery
    pdf_files = sorted(pdf_corpus.rglob("*.pdf"))
    assert len(pdf_files) == 2

    # 2. Parse each PDF
    docs = [parse_pdf(f) for f in pdf_files]
    assert all(d is not None for d in docs)

    # 3. Check the board manual
    board_doc = next(d for d in docs if "Board X" in d.title)
    assert len(board_doc.pages) == 2
    assert board_doc.pages[0].page_number == 1
    assert board_doc.pages[1].page_number == 2
    assert "Board X Manual" in board_doc.pages[0].text
    assert "Installation" in board_doc.pages[1].text
    assert board_doc.skipped_pages == 0

    # 4. Check the LED diagnostics
    led_doc = next(d for d in docs if "LED" in d.title)
    assert len(led_doc.pages) == 1
    assert "green" in led_doc.pages[0].text.lower()


def test_corrupt_pdf_skipped(tmp_path):
    """Corrupt files should return None, not crash."""
    from retriva.ingestion.pdf_parser import parse_pdf

    corrupt = tmp_path / "bad.pdf"
    corrupt.write_text("definitely not a PDF")
    assert parse_pdf(corrupt) is None


# ---------------------------------------------------------------------------
# Test: CLI flag
# ---------------------------------------------------------------------------

def test_cli_help_shows_pdf_injector():
    """Verify that --injector pdf is in the CLI help text."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "retriva.cli", "ingest", "--help"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src", "PATH": ""},
    )
    assert "pdf" in result.stdout
