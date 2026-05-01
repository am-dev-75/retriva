import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from retriva.ingestion_api.main import app

class TestDeleteDocument(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("retriva.ingestion_api.routers.documents.get_client")
    def test_delete_missing_document(self, mock_get_client):
        # Mock Qdrant client
        mock_qdrant = MagicMock()
        mock_get_client.return_value = mock_qdrant
        
        # Mock scroll to return no hits (document missing)
        mock_qdrant.scroll.return_value = ([], None)
        
        doc_id = "missing-doc"
        response = self.client.delete(f"/api/v1/documents/{doc_id}")
        
        self.assertEqual(response.status_code, 204)
        mock_qdrant.scroll.assert_called_once()
        # Ensure delete was NOT called if missing (based on my refined logic)
        mock_qdrant.delete.assert_not_called()

    @patch("retriva.ingestion_api.routers.documents.get_client")
    @patch("retriva.ingestion_api.routers.documents.delete_chunks_by_source_path")
    def test_delete_existing_document(self, mock_delete_chunks, mock_get_client):
        # Mock Qdrant client
        mock_qdrant = MagicMock()
        mock_get_client.return_value = mock_qdrant
        
        # Mock scroll to return a hit (document exists)
        mock_qdrant.scroll.return_value = ([MagicMock()], None)
        
        doc_id = "existing-doc"
        response = self.client.delete(f"/api/v1/documents/{doc_id}")
        
        self.assertEqual(response.status_code, 204)
        mock_qdrant.scroll.assert_called_once()
        mock_delete_chunks.assert_called_once_with(mock_qdrant, doc_id)

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
