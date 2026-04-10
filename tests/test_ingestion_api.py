import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock Qdrant connection during app startup Lifespan
@pytest.fixture(autouse=True)
def mock_qdrant_startup():
    with patch("retriva.ingestion_api.main.get_client"), \
         patch("retriva.ingestion_api.main.init_collection"):
        yield

from retriva.ingestion_api.main import app

@patch("retriva.ingestion_api.routers.ingest.upsert_chunks")
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

@patch("retriva.ingestion_api.routers.ingest_HTML.upsert_chunks")
def test_ingest_html(mock_upsert_chunks):
    payload = {
        "source_path": "test://html",
        "page_title": "Test HTML",
        "html_content": "<html><body><main>Extract this content</main></body></html>"
    }
    
    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/html", json=payload)
    
    assert response.status_code == 202
    assert mock_upsert_chunks.called
    chunks = mock_upsert_chunks.call_args[0][1]
    assert len(chunks) == 1
    assert chunks[0].text == "Extract this content"

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
