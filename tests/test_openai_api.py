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

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock Qdrant connection during app startup Lifespan
@pytest.fixture(autouse=True)
def mock_qdrant_startup():
    with patch("retriva.openai_api.main.get_client"), \
         patch("retriva.openai_api.main.init_collection"):
        yield

from retriva.openai_api.main import app


# ---------------------------------------------------------------------------
# GET /v1/models
# ---------------------------------------------------------------------------

def test_list_models():
    with TestClient(app) as client:
        response = client.get("/v1/models")

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "list"
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == "retriva"
    assert body["data"][0]["object"] == "model"
    assert body["data"][0]["owned_by"] == "retriva"


# ---------------------------------------------------------------------------
# POST /v1/chat/completions
# ---------------------------------------------------------------------------

@patch("retriva.openai_api.routers.chat_completions.ask_question")
def test_chat_completions_success(mock_ask):
    mock_ask.return_value = {
        "answer": "The board uses a Cortex-A53 processor [Document 1].",
        "retrieved_chunks": [
            {
                "doc_id": "wiki/board-overview",
                "source_path": "https://wiki.dave.eu/board-overview",
                "page_title": "Board Overview",
                "text": "The system-on-module features a Cortex-A53...",
            }
        ],
        "grounding": {"grounded": True},
    }

    payload = {
        "model": "retriva",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What processor does the board use?"},
        ],
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200
    body = response.json()

    # OpenAI structure
    assert body["object"] == "chat.completion"
    assert body["id"].startswith("chatcmpl-")
    assert body["model"] == "retriva"

    # Choices
    assert len(body["choices"]) == 1
    choice = body["choices"][0]
    assert choice["index"] == 0
    assert choice["finish_reason"] == "stop"
    assert "Cortex-A53" in choice["message"]["content"]
    assert choice["message"]["role"] == "assistant"

    # Citation metadata
    citations = choice["message"]["metadata"]["citations"]
    assert len(citations) == 1
    assert citations[0]["document_id"] == "wiki/board-overview"
    assert citations[0]["title"] == "Board Overview"

    # Usage
    assert body["usage"]["total_tokens"] > 0
    assert body["usage"]["total_tokens"] == (
        body["usage"]["prompt_tokens"] + body["usage"]["completion_tokens"]
    )


@patch("retriva.openai_api.routers.chat_completions.ask_question")
def test_chat_completions_no_user_message(mock_ask):
    """System-only messages — no user question — should return 400."""
    payload = {
        "model": "retriva",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
        ],
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 400
    assert "user" in response.json()["detail"].lower()
    mock_ask.assert_not_called()


def test_chat_completions_empty_messages():
    """Empty messages array should fail Pydantic validation (422)."""
    payload = {
        "model": "retriva",
        "messages": [],
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 422


@patch("retriva.openai_api.routers.chat_completions.ask_question")
def test_chat_completions_pipeline_error(mock_ask):
    """QA pipeline failure should return 500."""
    mock_ask.side_effect = RuntimeError("Embedding service unreachable")

    payload = {
        "model": "retriva",
        "messages": [
            {"role": "user", "content": "What is Retriva?"},
        ],
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 500
    assert "QA pipeline" in response.json()["detail"]


@patch("retriva.openai_api.routers.chat_completions.ask_question")
def test_chat_completions_deduplicates_citations(mock_ask):
    """Chunks from the same document should produce a single citation."""
    mock_ask.return_value = {
        "answer": "Answer referencing [Document 1].",
        "retrieved_chunks": [
            {"doc_id": "doc-1", "source_path": "/p/doc1", "page_title": "Doc 1", "text": "a"},
            {"doc_id": "doc-1", "source_path": "/p/doc1", "page_title": "Doc 1", "text": "b"},
            {"doc_id": "doc-2", "source_path": "/p/doc2", "page_title": "Doc 2", "text": "c"},
        ],
    }

    payload = {
        "model": "retriva",
        "messages": [{"role": "user", "content": "test"}],
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    citations = response.json()["choices"][0]["message"]["metadata"]["citations"]
    assert len(citations) == 2  # doc-1 and doc-2, not 3


# ---------------------------------------------------------------------------
# POST /v1/chat/completions — streaming (stream=true)
# ---------------------------------------------------------------------------

import json


def _parse_sse_events(raw_text: str) -> list:
    """Parse SSE text into a list of parsed JSON events + the [DONE] marker."""
    events = []
    for line in raw_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        assert line.startswith("data: "), f"SSE line missing 'data: ' prefix: {line!r}"
        payload = line[len("data: "):]
        if payload == "[DONE]":
            events.append("[DONE]")
        else:
            events.append(json.loads(payload))
    return events


@patch("retriva.openai_api.routers.chat_completions.ask_question_streaming")
def test_streaming_success(mock_stream):
    """stream=true should return SSE events with correct delta protocol."""
    mock_chunks = [
        {"doc_id": "doc-1", "source_path": "/p/doc1", "page_title": "Doc 1", "text": "ctx"},
    ]

    def fake_content_gen():
        yield "Hello"
        yield " world"
        yield "!"

    mock_stream.return_value = (mock_chunks, fake_content_gen())

    payload = {
        "model": "retriva",
        "messages": [{"role": "user", "content": "Hi"}],
        "stream": True,
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = _parse_sse_events(response.text)

    # Must have: role event + 3 content events + stop event + [DONE]
    assert len(events) == 6

    # First event: role announcement
    first = events[0]
    assert first["object"] == "chat.completion.chunk"
    assert first["choices"][0]["delta"]["role"] == "assistant"
    assert first["choices"][0]["delta"].get("content") is None
    assert first["choices"][0]["finish_reason"] is None
    completion_id = first["id"]
    assert completion_id.startswith("chatcmpl-")

    # Content events
    assert events[1]["choices"][0]["delta"]["content"] == "Hello"
    assert events[2]["choices"][0]["delta"]["content"] == " world"
    assert events[3]["choices"][0]["delta"]["content"] == "!"

    # All share the same ID
    for e in events[:-1]:  # exclude [DONE]
        assert e["id"] == completion_id

    # Stop event
    stop = events[4]
    assert stop["choices"][0]["finish_reason"] == "stop"
    assert stop["choices"][0]["delta"].get("content") is None

    # Terminator
    assert events[5] == "[DONE]"


@patch("retriva.openai_api.routers.chat_completions.ask_question_streaming")
def test_streaming_pipeline_error(mock_stream):
    """Pipeline error during streaming init should return 500."""
    mock_stream.side_effect = RuntimeError("Qdrant down")

    payload = {
        "model": "retriva",
        "messages": [{"role": "user", "content": "test"}],
        "stream": True,
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 500


@patch("retriva.openai_api.routers.chat_completions.ask_question_streaming")
def test_streaming_no_user_message(mock_stream):
    """stream=true with no user message should still return 400."""
    payload = {
        "model": "retriva",
        "messages": [{"role": "system", "content": "hi"}],
        "stream": True,
    }

    with TestClient(app) as client:
        response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 400
    mock_stream.assert_not_called()

