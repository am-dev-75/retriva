# Implementation Plan — Open WebUI Integration

## Phase 1: OpenAI Schemas

Create `src/retriva/openai_api/schemas.py`:
- `ChatMessage(role, content, metadata=None)` where metadata can hold `citations`
- `ChatCompletionRequest(model, messages: list[ChatMessage], stream=False, temperature=None, top_p=None)`
- `ChatChoice(index, message: ChatMessage, finish_reason)`
- `UsageInfo(prompt_tokens, completion_tokens, total_tokens)` — estimated from character counts
- `ChatCompletionResponse(id, object, created, model, choices, usage)`
- `ModelInfo(id, object, created, owned_by)`
- `ListModelsResponse(object, data: list[ModelInfo])`

## Phase 2: Models Endpoint

Create `src/retriva/openai_api/routers/models.py`:
- `GET /v1/models` → returns `ListModelsResponse` with one model: `{id: "retriva", object: "model", owned_by: "retriva"}`
- This satisfies Open WebUI's connection probe

## Phase 3: Chat Completions Endpoint

Create `src/retriva/openai_api/routers/chat_completions.py`:
- `POST /v1/chat/completions`
- Logic:
  1. Find the last message with `role == "user"` → this is the question
  2. Call `ask_question(question, settings.retriever_top_k)` (existing pipeline)
  3. Build `citations` list from `retrieved_chunks`: extract `source_path`, `page_title`, `doc_id`
  4. Construct `ChatCompletionResponse`:
     - `id` = `"chatcmpl-"` + uuid4
     - `object` = `"chat.completion"`
     - `choices[0].message.content` = answer text
     - `choices[0].message.metadata.citations` = citations list
     - `choices[0].finish_reason` = `"stop"`
     - `usage` = estimated from character lengths
  5. Return 200 OK

- Error handling:
  - Empty messages → 400
  - No user message found → 400
  - QA pipeline failure → 500 with error message in response

## Phase 4: App Setup

Create `src/retriva/openai_api/main.py`:
- Separate FastAPI app (not a sub-mount of the ingestion API)
- CORS middleware: allow all origins (Open WebUI may be on a different host)
- Qdrant lifespan: same pattern as `ingestion_api/main.py`

Create `src/retriva/openai_api/__main__.py`:
- `python -m retriva.openai_api` → runs uvicorn on `settings.openai_api_port` (default 8001)
- Prints version banner

Add to `config.py`: `openai_api_port: int = 8001`

## Phase 5: Testing

- **Unit tests** (`tests/test_openai_schemas.py`): serialization round-trips
- **API tests** (`tests/test_openai_api.py`):
  - `GET /v1/models` → 200, correct schema
  - `POST /v1/chat/completions` with valid request → 200, has `id`, `choices`, `usage`
  - `POST /v1/chat/completions` with empty messages → 400
  - Verify `metadata.citations` present when chunks have sources
- **Regression**: existing `test_ingestion_api.py` passes unchanged
- **Manual**: configure Open WebUI → Settings → Connections → add `http://<host>:8001/v1` → verify model appears → send a question → verify grounded answer
