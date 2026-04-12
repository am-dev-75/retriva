# Acceptance Criteria — Open WebUI Integration

## Functional — Chat Completions

- `POST /v1/chat/completions` accepts an OpenAI-format request and returns an
  OpenAI-format response
- The `messages` array is parsed; the last `user` message is used as the query
- The response includes `id`, `object: "chat.completion"`, `choices`, and `usage`
- The answer text contains `[Document N]` citations matching retrieved sources
- `choices[0].message.metadata.citations` contains structured source info
  (document_id, title, source URL)
- Unknown `model` values are accepted (Retriva always uses its configured
  backend model)
- `stream: true` is accepted but ignored (returns a non-streamed response)

## Functional — Models

- `GET /v1/models` returns an OpenAI-format model list with at least one entry
- The model entry has `id: "retriva"` and `object: "model"`

## Non-functional

- Open WebUI can connect using only a base URL (e.g., `http://retriva:8001/v1`)
  — no API key, no custom headers, no plugins
- Existing ingestion API (`/api/v1/ingest/*`) continues to work unchanged
- Existing QA pipeline (`ask_question`, `retrieve_top_chunks`, etc.) is not
  modified
- Both APIs can run simultaneously on different ports (8000 ingestion, 8001
  chat)
- CORS headers allow cross-origin requests from Open WebUI
