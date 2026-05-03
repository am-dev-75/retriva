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
Unit tests for the Tika REST client.

All tests mock the HTTP layer — no Tika server required.
"""

import pytest
from unittest.mock import patch, MagicMock

from retriva.ingestion.tika_client import TikaClient, TikaDetectionResult


class TestTikaDetectMime:
    """Tests for TikaClient.detect_mime()."""

    @patch("retriva.ingestion.tika_client.requests.put")
    def test_detect_pdf(self, mock_put, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "application/pdf"
        mock_resp.raise_for_status = MagicMock()
        mock_put.return_value = mock_resp

        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4 fake content")

        client = TikaClient(server_url="http://fake:9998")
        mime = client.detect_mime(str(f))
        assert mime == "application/pdf"

    @patch("retriva.ingestion.tika_client.requests.put")
    def test_detect_connection_error(self, mock_put, tmp_path):
        mock_put.side_effect = ConnectionError("refused")

        f = tmp_path / "test.pdf"
        f.write_bytes(b"content")

        client = TikaClient(server_url="http://fake:9998")
        mime = client.detect_mime(str(f))
        assert mime == "application/octet-stream"  # fallback


class TestTikaExtractMetadata:
    """Tests for TikaClient.extract_metadata()."""

    @patch("retriva.ingestion.tika_client.requests.put")
    def test_extract_metadata(self, mock_put, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "dc:title": "My Document",
            "pdf:totalChars": "5000",
            "dc:language": "en",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_put.return_value = mock_resp

        f = tmp_path / "test.pdf"
        f.write_bytes(b"content")

        client = TikaClient(server_url="http://fake:9998")
        meta = client.extract_metadata(str(f))
        assert meta["dc:title"] == "My Document"
        assert meta["pdf:totalChars"] == "5000"

    @patch("retriva.ingestion.tika_client.requests.put")
    def test_extract_metadata_list_response(self, mock_put, tmp_path):
        """Tika sometimes returns a list for multi-document files."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"dc:title": "First", "Content-Type": "application/pdf"}
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_put.return_value = mock_resp

        f = tmp_path / "test.pdf"
        f.write_bytes(b"content")

        client = TikaClient(server_url="http://fake:9998")
        meta = client.extract_metadata(str(f))
        assert meta["dc:title"] == "First"


class TestTikaDetect:
    """Tests for TikaClient.detect() — combined detection."""

    @patch("retriva.ingestion.tika_client.requests.put")
    def test_detect_scanned_pdf(self, mock_put, tmp_path):
        """PDF with totalChars=0 should be flagged as scanned."""
        responses = [
            # detect_mime response
            MagicMock(text="application/pdf", raise_for_status=MagicMock()),
            # extract_metadata response
            MagicMock(
                json=MagicMock(return_value={
                    "Content-Type": "application/pdf",
                    "pdf:totalChars": "0",
                }),
                raise_for_status=MagicMock(),
            ),
        ]
        mock_put.side_effect = responses

        f = tmp_path / "scan.pdf"
        f.write_bytes(b"content")

        client = TikaClient(server_url="http://fake:9998")
        result = client.detect(str(f))
        assert result.content_type == "application/pdf"
        assert result.is_scanned is True

    @patch("retriva.ingestion.tika_client.requests.put")
    def test_detect_text_pdf(self, mock_put, tmp_path):
        """PDF with many chars should NOT be flagged as scanned."""
        responses = [
            MagicMock(text="application/pdf", raise_for_status=MagicMock()),
            MagicMock(
                json=MagicMock(return_value={
                    "Content-Type": "application/pdf",
                    "pdf:totalChars": "12000",
                    "dc:language": "en",
                }),
                raise_for_status=MagicMock(),
            ),
        ]
        mock_put.side_effect = responses

        f = tmp_path / "text.pdf"
        f.write_bytes(b"content")

        client = TikaClient(server_url="http://fake:9998")
        result = client.detect(str(f))
        assert result.content_type == "application/pdf"
        assert result.is_scanned is False
        assert result.language == "en"


class TestTikaHealthCheck:
    """Tests for TikaClient.health_check()."""

    @patch("retriva.ingestion.tika_client.requests.get")
    def test_health_check_reachable(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)

        client = TikaClient(server_url="http://fake:9998")
        assert client.health_check() is True

    @patch("retriva.ingestion.tika_client.requests.get")
    def test_health_check_unreachable(self, mock_get):
        mock_get.side_effect = ConnectionError("refused")

        client = TikaClient(server_url="http://fake:9998")
        assert client.health_check() is False
