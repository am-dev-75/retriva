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
Unit tests for the Docling parser.

All tests mock the docling.DocumentConverter — no Docling models required.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from retriva.domain.models import CanonicalRecord


class TestDoclingParser:
    """Tests for DoclingParser.parse()."""

    def _make_parser(self):
        """Create a DoclingParser with a mocked converter."""
        # We need to mock the import of docling inside the lazy init
        from retriva.ingestion.docling_parser import DoclingParser
        parser = DoclingParser()
        return parser

    def _mock_item(self, label, text, page_no=1):
        """Create a mock Docling document item."""
        item = MagicMock()
        item.label = label
        item.text = text
        item.export_to_markdown.return_value = text

        # Mock provenance
        prov_entry = MagicMock()
        prov_entry.page_no = page_no
        prov_entry.bbox = None
        item.prov = [prov_entry]
        item.parent = None
        item.image = None

        return item

    @patch("retriva.ingestion.docling_parser.DoclingParser._get_converter")
    def test_parse_returns_canonical_records(self, mock_get_converter, tmp_path):
        # Create a mock Docling result
        mock_doc = MagicMock()
        items = [
            self._mock_item("title", "Chapter 1: Introduction"),
            self._mock_item("paragraph", "This is the introduction text."),
            self._mock_item("paragraph", "More content here."),
        ]
        mock_doc.iterate_items.return_value = iter(items)

        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        f = tmp_path / "test.pdf"
        f.write_bytes(b"content")

        parser = self._make_parser()
        parser._converter = mock_converter
        records = parser.parse(str(f), "application/pdf")

        assert len(records) == 3
        assert all(isinstance(r, CanonicalRecord) for r in records)
        assert records[0].element_type == "heading"
        assert records[0].text == "Chapter 1: Introduction"
        assert records[1].element_type == "text"
        assert all(r.parser_name == "docling" for r in records)

    @patch("retriva.ingestion.docling_parser.DoclingParser._get_converter")
    def test_table_element_type(self, mock_get_converter, tmp_path):
        mock_doc = MagicMock()
        table_item = self._mock_item("table", "| A | B |\n|---|---|\n| 1 | 2 |")
        table_item.export_to_html.return_value = "<table><tr><td>1</td></tr></table>"
        mock_doc.iterate_items.return_value = iter([table_item])

        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        f = tmp_path / "test.pdf"
        f.write_bytes(b"content")

        parser = self._make_parser()
        parser._converter = mock_converter
        records = parser.parse(str(f), "application/pdf")

        assert len(records) == 1
        assert records[0].element_type == "table"
        assert records[0].table_html is not None

    @patch("retriva.ingestion.docling_parser.DoclingParser._get_converter")
    def test_empty_items_skipped(self, mock_get_converter, tmp_path):
        mock_doc = MagicMock()
        items = [
            self._mock_item("paragraph", ""),  # empty
            self._mock_item("paragraph", "   "),  # whitespace only
            self._mock_item("paragraph", "Valid content"),
        ]
        mock_doc.iterate_items.return_value = iter(items)

        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        f = tmp_path / "test.pdf"
        f.write_bytes(b"content")

        parser = self._make_parser()
        parser._converter = mock_converter
        records = parser.parse(str(f), "application/pdf")

        assert len(records) == 1
        assert records[0].text == "Valid content"

    @patch("retriva.ingestion.docling_parser.DoclingParser._get_converter")
    def test_fallback_markdown_export(self, mock_get_converter, tmp_path):
        """When iterate_items() is not available, fall back to markdown export."""
        mock_doc = MagicMock()
        mock_doc.iterate_items.side_effect = AttributeError("no iterate_items")
        mock_doc.export_to_markdown.return_value = "# Fallback\n\nSome text."

        mock_result = MagicMock()
        mock_result.document = mock_doc

        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result
        mock_get_converter.return_value = mock_converter

        f = tmp_path / "test.pdf"
        f.write_bytes(b"content")

        parser = self._make_parser()
        parser._converter = mock_converter
        records = parser.parse(str(f), "application/pdf")

        assert len(records) == 1
        assert records[0].text == "# Fallback\n\nSome text."
        assert records[0].parser_name == "docling"
