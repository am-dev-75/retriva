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
PDF text extraction with pluggable backend.

The default implementation uses ``pdfplumber`` (pure Python, MIT license).
Alternative backends (e.g., pymupdf) can be swapped by registering a
higher-priority ``PdfExtractor`` implementation in the capability registry.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pdfplumber

from retriva.logger import get_logger
from retriva.registry import CapabilityRegistry

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PdfPage:
    """A single page extracted from a PDF file."""
    page_number: int    # 1-indexed
    text: str           # extracted text for this page


@dataclass
class PdfDocument:
    """A parsed PDF with page-by-page text and metadata."""
    title: str              # derived title
    source_path: str        # absolute path to the PDF
    pages: list[PdfPage]    # non-empty pages only
    total_pages: int        # total pages in the PDF
    skipped_pages: int      # pages with no extractable text


# ---------------------------------------------------------------------------
# Default pdfplumber backend
# ---------------------------------------------------------------------------

class PdfPlumberExtractor:
    """Default PdfExtractor using pdfplumber (pure Python, MIT license)."""

    def extract_pages(self, pdf_path: Path) -> list[dict] | None:
        """
        Extract text page-by-page from a PDF file.

        Returns a list of ``{"page_number": int, "text": str}`` dicts
        for pages with extractable text, or ``None`` if the PDF cannot
        be opened (encrypted, corrupt, etc.).
        """
        try:
            pdf = pdfplumber.open(pdf_path)
        except Exception as e:
            logger.warning(f"Cannot open PDF '{pdf_path}': {e}")
            return None

        pages = []
        try:
            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    logger.debug(f"Error extracting page {i + 1} from '{pdf_path}': {e}")
                    text = ""

                text = text.strip()
                if text:
                    pages.append({"page_number": i + 1, "text": text})
                else:
                    logger.debug(
                        f"Page {i + 1} of '{pdf_path}' has no extractable text — skipping."
                    )
        finally:
            pdf.close()

        return pages

    def extract_metadata(self, pdf_path: Path) -> dict[str, str]:
        """Return PDF metadata (Title, Author, etc.) as a dict."""
        try:
            pdf = pdfplumber.open(pdf_path)
            metadata = pdf.metadata or {}
            pdf.close()
            # Normalise keys to strings, filter None values
            return {str(k): str(v) for k, v in metadata.items() if v is not None}
        except Exception as e:
            logger.debug(f"Cannot read metadata from '{pdf_path}': {e}")
            return {}


# Register as default implementation at priority 100
CapabilityRegistry().register("pdf_extractor", PdfPlumberExtractor, priority=100)


# ---------------------------------------------------------------------------
# Title derivation
# ---------------------------------------------------------------------------

_RE_HEADING = re.compile(r"^[A-Z][A-Za-z0-9 :—\-–/]{5,80}$", re.MULTILINE)


def derive_title(
    metadata: dict[str, str],
    first_page_text: str,
    pdf_path: Path,
) -> str:
    """
    Derive a human-readable document title with fallback chain:

    1. PDF metadata ``Title`` field (if non-empty and not a generic path)
    2. First heading-like line from page 1 text
    3. Filename stem as fallback
    """
    # 1. PDF metadata title
    meta_title = metadata.get("Title", "").strip()
    if meta_title and not meta_title.startswith("/") and len(meta_title) > 3:
        return meta_title

    # 2. First heading-like line from page 1
    if first_page_text:
        match = _RE_HEADING.search(first_page_text[:500])
        if match:
            return match.group(0).strip()

    # 3. Filename stem
    return pdf_path.stem.replace("_", " ").replace("-", " ").title()


# ---------------------------------------------------------------------------
# High-level parsing function
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: Path) -> Optional[PdfDocument]:
    """
    Parse a PDF file into a :class:`PdfDocument` using the registry-resolved
    ``PdfExtractor``.

    Returns ``None`` if the PDF is unreadable (encrypted, corrupt).
    """
    registry = CapabilityRegistry()
    try:
        extractor = registry.get_instance("pdf_extractor")
    except KeyError:
        # Fallback: registry may have been reset (e.g. in tests)
        extractor = PdfPlumberExtractor()

    raw_pages = extractor.extract_pages(pdf_path)
    if raw_pages is None:
        return None

    metadata = extractor.extract_metadata(pdf_path)

    # Build PdfPage objects
    pages = [PdfPage(page_number=p["page_number"], text=p["text"]) for p in raw_pages]

    # Count total pages (we need to open the PDF briefly)
    total_pages = 0
    try:
        pdf = pdfplumber.open(pdf_path)
        total_pages = len(pdf.pages)
        pdf.close()
    except Exception:
        total_pages = len(pages)  # best effort

    skipped = total_pages - len(pages)
    first_page_text = pages[0].text if pages else ""
    title = derive_title(metadata, first_page_text, pdf_path)

    return PdfDocument(
        title=title,
        source_path=str(pdf_path.resolve()),
        pages=pages,
        total_pages=total_pages,
        skipped_pages=skipped,
    )
