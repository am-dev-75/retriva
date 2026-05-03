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
Unit tests for CanonicalRecord → ParsedDocument conversion.
"""

import pytest

from retriva.domain.models import CanonicalRecord, ParsedDocument


class TestRecordsToParsedDocument:
    """Tests for records_to_parsed_document()."""

    def _convert(self, records, **kwargs):
        from retriva.ingestion_api.routers.v2_documents import records_to_parsed_document
        return records_to_parsed_document(records, **kwargs)

    def test_text_records_concatenated(self):
        records = [
            CanonicalRecord(
                document_id="test", element_type="text",
                text="First paragraph.", source_uri="test.txt",
                parser_name="docling",
            ),
            CanonicalRecord(
                document_id="test", element_type="text",
                text="Second paragraph.", source_uri="test.txt",
                parser_name="docling",
            ),
        ]
        doc = self._convert(
            records, source_uri="test.txt", metadata=None,
        )
        assert isinstance(doc, ParsedDocument)
        assert "First paragraph." in doc.content_text
        assert "Second paragraph." in doc.content_text

    def test_heading_records_become_markdown(self):
        records = [
            CanonicalRecord(
                document_id="test", element_type="heading",
                text="Introduction", heading_path=[],
                source_uri="test.txt", parser_name="docling",
            ),
        ]
        doc = self._convert(records, source_uri="test.txt", metadata=None)
        assert "# Introduction" in doc.content_text

    def test_table_markdown_preserved(self):
        records = [
            CanonicalRecord(
                document_id="test", element_type="table",
                text="fallback",
                table_markdown="| A | B |\n|---|---|\n| 1 | 2 |",
                source_uri="test.txt", parser_name="docling",
            ),
        ]
        doc = self._convert(records, source_uri="test.txt", metadata=None)
        assert "| A | B |" in doc.content_text

    def test_image_records_become_images(self):
        records = [
            CanonicalRecord(
                document_id="test", element_type="image",
                text="A diagram of a circuit",
                image_path="/tmp/circuit.png",
                source_uri="test.pdf", parser_name="docling",
            ),
        ]
        doc = self._convert(records, source_uri="test.pdf", metadata=None)
        assert len(doc.images) == 1
        assert doc.images[0].vlm_description == "A diagram of a circuit"

    def test_metadata_propagated(self):
        records = [
            CanonicalRecord(
                document_id="test", element_type="text",
                text="Content", source_uri="test.txt",
                parser_name="docling",
            ),
        ]
        metadata = {"tenant": "A", "project": "retriva"}
        doc = self._convert(
            records, source_uri="test.txt", metadata=metadata,
        )
        assert doc.user_metadata == {"tenant": "A", "project": "retriva"}

    def test_title_from_first_heading(self):
        records = [
            CanonicalRecord(
                document_id="test", element_type="heading",
                text="My Title", source_uri="test.txt",
                parser_name="docling",
            ),
            CanonicalRecord(
                document_id="test", element_type="text",
                text="Content", source_uri="test.txt",
                parser_name="docling",
            ),
        ]
        doc = self._convert(
            records, source_uri="test.txt", metadata=None,
        )
        assert doc.page_title == "My Title"

    def test_title_from_filename_fallback(self):
        records = [
            CanonicalRecord(
                document_id="test", element_type="text",
                text="Content", source_uri="/path/to/my_document.pdf",
                parser_name="docling",
            ),
        ]
        doc = self._convert(
            records, source_uri="/path/to/my_document.pdf", metadata=None,
        )
        assert doc.page_title == "My Document"
