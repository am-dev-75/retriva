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
Parser router for the v2 ingestion pipeline.

Detects document MIME type and dispatches to the appropriate parser
backend. Explicit ``content_type`` hints take precedence over
extension-based detection.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from retriva.domain.models import ImageContext
from retriva.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Parser result
# ---------------------------------------------------------------------------

@dataclass
class ParserResult:
    """Structured output from a parser."""

    content_text: str
    page_title: str
    language: str = "en"
    images: List[ImageContext] = field(default_factory=list)
    pages: Optional[List[Dict]] = None  # For multi-page docs (PDF)


# ---------------------------------------------------------------------------
# Default parser router
# ---------------------------------------------------------------------------

# Extension → MIME mapping for auto-detection
_MIME_MAP: Dict[str, str] = {
    ".txt": "text/plain",
    ".text": "text/plain",
    ".log": "text/plain",
    ".html": "text/html",
    ".htm": "text/html",
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}


class DefaultParserRouter:
    """Routes documents to parsers based on MIME type.

    MIME detection order:
    1. Explicit ``content_type`` hint (if provided)
    2. File extension mapping
    3. Fallback to ``application/octet-stream`` (treated as plain text)
    """

    def detect_content_type(
        self,
        source_uri: str,
        hint: Optional[str] = None,
    ) -> str:
        """Determine MIME type from explicit hint or URI extension.

        Args:
            source_uri: Path or URI to the document.
            hint: Explicit MIME type hint — takes precedence if provided.

        Returns:
            Detected MIME type string.
        """
        if hint:
            return hint
        ext = Path(source_uri).suffix.lower()
        detected = _MIME_MAP.get(ext, "application/octet-stream")
        logger.debug(f"Detected MIME type for '{source_uri}': {detected}")
        return detected

    def parse(
        self,
        source: str,
        content_type: str,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> ParserResult:
        """Dispatch to the correct parser based on MIME type.

        Args:
            source: Local file path to the document.
            content_type: MIME type (from detection or explicit hint).
            cancel_check: Optional cancellation callback.

        Returns:
            A ``ParserResult`` with extracted content.
        """
        if content_type == "application/pdf":
            return self._parse_pdf(source, cancel_check)
        elif content_type in ("text/html",):
            return self._parse_html(source)
        elif content_type in ("text/markdown",):
            return self._parse_markdown(source)
        else:
            # Default: treat as plain text
            return self._parse_text(source)

    # -- Parser delegates --------------------------------------------------

    def _parse_text(self, source: str) -> ParserResult:
        """Read a plain-text file."""
        path = Path(source)
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading text file '{source}': {e}")
            text = ""
        title = path.stem.replace("_", " ").replace("-", " ").title()
        return ParserResult(content_text=text, page_title=title)

    def _parse_html(self, source: str) -> ParserResult:
        """Parse an HTML file using the registered HTMLParser."""
        path = Path(source)
        try:
            html = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading HTML file '{source}': {e}")
            return ParserResult(content_text="", page_title=path.stem)

        from retriva.registry import CapabilityRegistry
        import retriva.ingestion.html_parser  # noqa: F401 — triggers registration

        registry = CapabilityRegistry()
        html_parser = registry.get_instance("html_parser")

        content = html_parser.extract_content(html) or ""
        language = html_parser.extract_language(html)

        # Derive title from HTML
        from retriva.ingestion.html_parser import extract_title
        title = extract_title(html) or path.stem

        return ParserResult(
            content_text=content,
            page_title=title,
            language=language,
        )

    def _parse_pdf(
        self,
        source: str,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> ParserResult:
        """Parse a PDF file using the registered PdfExtractor."""
        from retriva.ingestion.pdf_parser import parse_pdf

        path = Path(source)
        doc = parse_pdf(path)
        if doc is None:
            logger.warning(f"Unreadable PDF: {source}")
            return ParserResult(
                content_text="",
                page_title=path.stem,
            )

        # Build per-page list for multi-page handling
        pages = [
            {"page_number": p.page_number, "text": p.text}
            for p in doc.pages
        ]

        # Concatenate all pages for single-document content
        full_text = "\n\n".join(p.text for p in doc.pages)

        return ParserResult(
            content_text=full_text,
            page_title=doc.title,
            pages=pages,
        )

    def _parse_markdown(self, source: str) -> ParserResult:
        """Parse a Markdown file."""
        from retriva.ingestion.markdown_parser import parse_markdown

        path = Path(source)
        result = parse_markdown(path)
        if result is None:
            logger.warning(f"Failed to parse Markdown: {source}")
            return ParserResult(
                content_text="",
                page_title=path.stem,
            )

        # Concatenate all sections into a single text
        section_texts = []
        for section in result["sections"]:
            heading = section.get("heading", "")
            content = section.get("content", "")
            if heading:
                section_texts.append(f"## {heading}\n\n{content}")
            else:
                section_texts.append(content)
        full_text = "\n\n".join(section_texts)

        return ParserResult(
            content_text=full_text,
            page_title=result["title"],
        )


# ---------------------------------------------------------------------------
# Register in CapabilityRegistry
# ---------------------------------------------------------------------------

from retriva.registry import CapabilityRegistry

CapabilityRegistry().register("parser_router", DefaultParserRouter, priority=100)
