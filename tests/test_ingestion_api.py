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

from retriva.ingestion_api.main import app

@patch("retriva.ingestion_api.routers.ingest_text.upsert_chunks")
def test_ingest_text(mock_upsert_chunks):
    payload = {
        "source_path": "test://doc",
        "page_title": "Test Doc",
        "content_text": "This is a simple plain text injection test."
    }
    
    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/text", json=payload)
    
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    
    assert mock_upsert_chunks.called
    chunks = mock_upsert_chunks.call_args[0][1]
    assert len(chunks) == 1
    assert chunks[0].text == "This is a simple plain text injection test."

@patch("retriva.ingestion_api.routers.ingest_HTML.enrich_images_with_vlm")
@patch("retriva.ingestion_api.routers.ingest_HTML.upsert_chunks")
def test_ingest_html_with_image(mock_upsert_chunks, mock_vlm_enrich):
    payload = {
        "source_path": "test://html",
        "page_title": "Test HTML",
        "html_content": "<html><body><main>Extract this content<figure><img src='test.jpg' alt='Test image'/><figcaption>Caption text</figcaption></figure></main></body></html>",
        "origin_file_path": "/tmp/test.html"
    }
    
    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/html", json=payload)
    
    assert response.status_code == 202
    assert mock_upsert_chunks.called
    assert mock_vlm_enrich.called
    
    chunks = mock_upsert_chunks.call_args[0][1]
    assert len(chunks) == 2
    
    text_chunks = [c for c in chunks if c.metadata.chunk_type == "text"]
    assert len(text_chunks) == 1
    assert "Extract this content" in text_chunks[0].text
    
    img_chunks = [c for c in chunks if c.metadata.chunk_type == "image"]
    assert len(img_chunks) == 1
    assert "Image: test.jpg" in img_chunks[0].text
    assert img_chunks[0].metadata.image_path == "test.jpg"

@patch("retriva.ingestion.vlm_describer.describe_image")
@patch("retriva.ingestion_api.routers.ingest_image.upsert_chunks")
def test_ingest_standalone_image(mock_upsert_chunks, mock_describe):
    mock_describe.return_value = "A detailed schematic showing pin connections."
    
    payload = {
        "source_path": "/images/schematic.png",
        "page_title": "schematic",
        "file_path": "/tmp/schematic.png"
    }
    
    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/image", json=payload)
    
    assert response.status_code == 202
    assert mock_upsert_chunks.called
    
    chunks = mock_upsert_chunks.call_args[0][1]
    assert len(chunks) == 1
    assert chunks[0].metadata.chunk_type == "image"
    assert "Description: A detailed schematic showing pin connections." in chunks[0].text

@patch("retriva.ingestion_api.routers.ingest.upsert_chunks")
def test_ingest_chunks(mock_upsert_chunks):
    payload = {
        "chunks": [
            {
                "text": "Chunk 1",
                "metadata": {
                    "doc_id": "doc1",
                    "source_path": "test://chunks",
                    "page_title": "Chunks",
                    "section_path": "",
                    "chunk_id": "chunk_1",
                    "chunk_index": 0,
                    "chunk_type": "text",
                    "language": "en"
                }
            }
        ]
    }
    
    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/chunks", json=payload)
    
    assert response.status_code == 202
    assert mock_upsert_chunks.called
    chunks = mock_upsert_chunks.call_args[0][1]
    assert len(chunks) == 1
    assert chunks[0].text == "Chunk 1"
