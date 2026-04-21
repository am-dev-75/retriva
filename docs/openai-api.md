# Retriva OpenAI-Compatible API Reference

Retriva provides an OpenAI-compatible API that allows it to be used as a drop-in replacement for OpenAI in tools like **Open WebUI**, **Dify**, or custom applications.

## Base URL
Default: `http://127.0.0.1:8001/v1`

## Endpoints

### 1. List Models
`GET /models`

Returns the list of available models. Retriva always exposes itself as a single unified model named `retriva`.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "retriva",
      "object": "model",
      "created": 1713725753,
      "owned_by": "retriva"
    }
  ]
}
```

### 2. Chat Completions
`POST /chat/completions`

Generates an assistant response for a given set of messages using RAG (Retrieval-Augmented Generation).

**Payload:**
```json
{
  "model": "retriva",
  "messages": [
    {"role": "user", "content": "What are the core components of Retriva?"}
  ],
  "stream": false
}
```

**Retriva-Specific Extensions:**
- **RAG Bypass**: If the message content starts with `### Task:`, Retriva will bypass the retrieval stage and answer directly using the LLM's internal knowledge.
- **Streaming Citations**: When `stream: true` is used, Retriva sends citations and metadata in the final chunk of the SSE stream.

**Response (Non-Streaming):**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1713725753,
  "model": "retriva",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Retriva consists of several components: the Ingestion API [1] and the OpenAI API [2].",
        "metadata": {
          "sources": [...],
          "citation_refs": [...],
          "output_text": "..."
        },
        "tool_calls": [...]
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 45,
    "total_tokens": 57
  }
}
```

## Citation Format
Retriva uses a specialized citation format compatible with Open WebUI.

### Sources
The `sources` (or `metadata.sources`) array contains unique documents retrieved from the index.
```json
{
  "source": {"name": "Architecture Doc"},
  "document": ["Text fragment 1", "Text fragment 2"],
  "metadata": [{"source": "/path/to/file.md", "title": "Architecture Doc"}]
}
```

### Citation References
The `citation_refs` array maps segments of the response text to specific citations.
```json
{
  "start_index": 0,
  "end_index": 45,
  "citation_index": 0
}
```

## Streaming Protocol
Retriva follows the standard OpenAI SSE (Server-Sent Events) delta protocol.

1.  **Role Event**: Announces `{"delta": {"role": "assistant"}}`.
2.  **Content Events**: Incremental deltas `{"delta": {"content": "..."}}`.
3.  **Final Event**: Includes `finish_reason: "stop"` and the full `metadata` (citations).
4.  **Done Event**: `data: [DONE]`.
