# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

"""
Tests for SDD 014 — User-Provided Metadata in ingestion_api_v1.

Covers:
- Metadata propagation to chunks (all endpoints)
- Backward compatibility (no metadata → None, no crash)
- Hard-limit validation (key count, value length, serialized size)
- Chunk bypass (raw /chunks endpoint)
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Ensure default implementations are registered before app is imported
import retriva.ingestion.chunker       # noqa: F401
import retriva.ingestion.html_parser   # noqa: F401
import retriva.ingestion.vlm_describer # noqa: F401

# Mock Qdrant connection during app startup Lifespan
@pytest.fixture(autouse=True)
def mock_qdrant_startup():
    with patch("retriva.ingestion_api.main.get_client"), \
         patch("retriva.ingestion_api.main.init_collection"):
        yield

@pytest.fixture(autouse=True)
def ensure_registry_defaults():
    """Re-register defaults in case earlier tests reset the singleton."""
    from retriva.registry import CapabilityRegistry
    from retriva.ingestion.chunker import DefaultChunker
    from retriva.ingestion.html_parser import DefaultHTMLParser
    from retriva.ingestion.vlm_describer import DefaultVLMDescriber
    registry = CapabilityRegistry()
    registry.register("chunker", DefaultChunker, priority=100)
    registry.register("html_parser", DefaultHTMLParser, priority=100)
    registry.register("vlm_describer", DefaultVLMDescriber, priority=100)
    yield

from retriva.ingestion_api.main import app

SAMPLE_METADATA = {"author": "Alice", "version": "2.0"}


# =========================================================================
# Propagation tests — metadata reaches every chunk
# =========================================================================

class TestMetadataPropagation:
    """Metadata supplied in the request must appear on every chunk."""

    @patch("retriva.ingestion_api.routers.ingest_text.upsert_chunks")
    def test_text_propagation(self, mock_upsert):
        payload = {
            "source_path": "test://text",
            "page_title": "Test",
            "content_text": "Hello world",
            "user_metadata": SAMPLE_METADATA,
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/text", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata == SAMPLE_METADATA

    @patch("retriva.ingestion_api.routers.ingest_HTML.enrich_images_with_vlm")
    @patch("retriva.ingestion_api.routers.ingest_HTML.upsert_chunks")
    def test_html_propagation(self, mock_upsert, mock_vlm):
        payload = {
            "source_path": "test://html",
            "page_title": "Test HTML",
            "html_content": "<html><body><main>Content</main></body></html>",
            "user_metadata": SAMPLE_METADATA,
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/html", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata == SAMPLE_METADATA

    @patch("retriva.ingestion_api.routers.ingest_pdf.upsert_chunks")
    def test_pdf_propagation(self, mock_upsert):
        payload = {
            "source_path": "/test.pdf",
            "page_title": "Test PDF",
            "content_text": "PDF content here",
            "page_number": 1,
            "total_pages": 1,
            "user_metadata": SAMPLE_METADATA,
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/pdf", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata == SAMPLE_METADATA

    @patch("retriva.ingestion_api.routers.ingest_mediawiki.upsert_chunks")
    def test_mediawiki_propagation(self, mock_upsert):
        payload = {
            "source_path": "/export.xml",
            "page_title": "Wiki Page",
            "content_text": "Wiki content",
            "page_id": 1,
            "namespace": 0,
            "user_metadata": SAMPLE_METADATA,
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/mediawiki", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata == SAMPLE_METADATA

    @patch("retriva.ingestion_api.routers.ingest_markdown.upsert_chunks")
    def test_markdown_propagation(self, mock_upsert):
        payload = {
            "source_path": "/test.md",
            "page_title": "Test MD",
            "sections": [
                {"heading": "Intro", "content": "Introduction text"},
                {"heading": "Body", "content": "Body text"},
            ],
            "user_metadata": SAMPLE_METADATA,
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/markdown", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata == SAMPLE_METADATA

    @patch("retriva.ingestion.vlm_describer.describe_image")
    @patch("retriva.ingestion_api.routers.ingest_image.upsert_chunks")
    def test_image_propagation(self, mock_upsert, mock_describe):
        mock_describe.return_value = "A test image."
        payload = {
            "source_path": "/img.png",
            "page_title": "image",
            "file_path": "/tmp/img.png",
            "user_metadata": SAMPLE_METADATA,
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/image", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata == SAMPLE_METADATA


# =========================================================================
# Backward compatibility — no metadata means None, not crash
# =========================================================================

class TestBackwardCompatibility:
    """Existing clients not providing user_metadata must continue to work."""

    @patch("retriva.ingestion_api.routers.ingest_text.upsert_chunks")
    def test_text_no_metadata(self, mock_upsert):
        payload = {
            "source_path": "test://text",
            "page_title": "Test",
            "content_text": "Hello world",
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/text", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata is None

    @patch("retriva.ingestion_api.routers.ingest_HTML.enrich_images_with_vlm")
    @patch("retriva.ingestion_api.routers.ingest_HTML.upsert_chunks")
    def test_html_no_metadata(self, mock_upsert, mock_vlm):
        payload = {
            "source_path": "test://html",
            "page_title": "Test HTML",
            "html_content": "<html><body><main>Content</main></body></html>",
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/html", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata is None

    @patch("retriva.ingestion_api.routers.ingest_pdf.upsert_chunks")
    def test_pdf_no_metadata(self, mock_upsert):
        payload = {
            "source_path": "/test.pdf",
            "page_title": "Test PDF",
            "content_text": "PDF content",
            "page_number": 1,
            "total_pages": 1,
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/pdf", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata is None

    @patch("retriva.ingestion_api.routers.ingest_mediawiki.upsert_chunks")
    def test_mediawiki_no_metadata(self, mock_upsert):
        payload = {
            "source_path": "/export.xml",
            "page_title": "Wiki Page",
            "content_text": "Wiki content",
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/mediawiki", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata is None

    @patch("retriva.ingestion_api.routers.ingest_markdown.upsert_chunks")
    def test_markdown_no_metadata(self, mock_upsert):
        payload = {
            "source_path": "/test.md",
            "page_title": "Test MD",
            "sections": [{"heading": "Intro", "content": "Text"}],
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/markdown", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        for chunk in mock_upsert.call_args[0][1]:
            assert chunk.metadata.user_metadata is None

    @patch("retriva.ingestion_api.routers.ingest.upsert_chunks")
    def test_chunks_no_metadata(self, mock_upsert):
        """Raw /chunks endpoint — existing payloads without user_metadata."""
        payload = {
            "chunks": [{
                "text": "Chunk 1",
                "metadata": {
                    "doc_id": "d1",
                    "source_path": "test://chunks",
                    "page_title": "Chunks",
                    "section_path": "",
                    "chunk_id": "c1",
                    "chunk_index": 0,
                    "chunk_type": "text",
                    "language": "en",
                },
            }],
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/chunks", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        chunks = mock_upsert.call_args[0][1]
        assert chunks[0].metadata.user_metadata is None


# =========================================================================
# Validation rejection — 422 with structured error payload
# =========================================================================

class TestMetadataValidation:
    """Hard-limit violations must produce 422 with structured details."""

    def _post_text(self, client, user_metadata):
        return client.post("/api/v1/ingest/text", json={
            "source_path": "test://val",
            "page_title": "Val",
            "content_text": "content",
            "user_metadata": user_metadata,
        })

    def test_non_string_value_rejected(self):
        with TestClient(app) as client:
            resp = self._post_text(client, {"key": 123})
        assert resp.status_code == 422

    def test_too_many_keys_rejected(self):
        metadata = {f"k{i}": "v" for i in range(25)}
        with TestClient(app) as client:
            resp = self._post_text(client, metadata)
        assert resp.status_code == 422
        # Ensure structured error mentions the limit
        body = resp.json()
        detail_str = json.dumps(body)
        assert "20" in detail_str or "keys" in detail_str.lower()

    def test_value_too_long_rejected(self):
        metadata = {"longval": "x" * 300}
        with TestClient(app) as client:
            resp = self._post_text(client, metadata)
        assert resp.status_code == 422
        body = resp.json()
        detail_str = json.dumps(body)
        assert "256" in detail_str or "characters" in detail_str.lower()

    def test_serialized_size_rejected(self):
        # Each value is 255 chars (within per-value limit) but 20 keys × ~260 bytes > 4096
        metadata = {f"key{i:02d}": "a" * 255 for i in range(20)}
        with TestClient(app) as client:
            resp = self._post_text(client, metadata)
        assert resp.status_code == 422
        body = resp.json()
        detail_str = json.dumps(body)
        assert "4096" in detail_str or "bytes" in detail_str.lower()

    def test_valid_metadata_accepted(self):
        """Metadata within all limits should be accepted."""
        metadata = {"author": "Alice", "version": "2.0"}
        with TestClient(app) as client:
            resp = self._post_text(client, metadata)
        assert resp.status_code == 202

    def test_empty_metadata_accepted(self):
        """Empty dict {} is valid metadata."""
        with TestClient(app) as client:
            resp = self._post_text(client, {})
        assert resp.status_code == 202

    def test_null_metadata_accepted(self):
        """Explicit null metadata is fine."""
        with TestClient(app) as client:
            resp = self._post_text(client, None)
        assert resp.status_code == 202


# =========================================================================
# Chunk bypass — /chunks with pre-baked user_metadata
# =========================================================================

class TestChunkBypass:
    """Raw /chunks endpoint passes through user_metadata from ChunkMetadata."""

    @patch("retriva.ingestion_api.routers.ingest.upsert_chunks")
    def test_chunks_with_user_metadata(self, mock_upsert):
        payload = {
            "chunks": [{
                "text": "Pre-baked chunk",
                "metadata": {
                    "doc_id": "d1",
                    "source_path": "test://chunks",
                    "page_title": "Chunks",
                    "section_path": "",
                    "chunk_id": "c1",
                    "chunk_index": 0,
                    "chunk_type": "text",
                    "language": "en",
                    "user_metadata": {"custom": "value"},
                },
            }],
        }
        with TestClient(app) as client:
            resp = client.post("/api/v1/ingest/chunks", json=payload)
        assert resp.status_code == 202
        assert mock_upsert.called
        chunks = mock_upsert.call_args[0][1]
        assert chunks[0].metadata.user_metadata == {"custom": "value"}


# =========================================================================
# Qdrant payload inclusion — model_dump includes user_metadata
# =========================================================================

class TestQdrantPayload:
    """Verify that model_dump() on ChunkMetadata includes user_metadata."""

    def test_model_dump_with_metadata(self):
        from retriva.domain.models import ChunkMetadata
        meta = ChunkMetadata(
            doc_id="d1",
            source_path="/test",
            page_title="Test",
            section_path="",
            chunk_id="c1",
            chunk_index=0,
            user_metadata={"author": "Alice"},
        )
        dump = meta.model_dump()
        assert dump["user_metadata"] == {"author": "Alice"}

    def test_model_dump_without_metadata(self):
        from retriva.domain.models import ChunkMetadata
        meta = ChunkMetadata(
            doc_id="d1",
            source_path="/test",
            page_title="Test",
            section_path="",
            chunk_id="c1",
            chunk_index=0,
        )
        dump = meta.model_dump()
        assert dump["user_metadata"] is None
