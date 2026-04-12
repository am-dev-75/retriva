# Tasks — Open WebUI Integration

## Phase 1: OpenAI Schemas
- [ ] Create `src/retriva/openai_api/schemas.py` with `ChatCompletionRequest`, `ChatMessage`, `ChatCompletionResponse`, `ChatChoice`, `UsageInfo`, `ModelInfo`, `ListModelsResponse`
- [ ] Unit test: validate request/response round-trip serialization

## Phase 2: Models Endpoint
- [ ] Create `src/retriva/openai_api/routers/models.py` with `GET /v1/models`
- [ ] Returns fixed model list: `[{id: "retriva", object: "model", ...}]`
- [ ] API test: verify OpenAI-format response structure

## Phase 3: Chat Completions Endpoint
- [ ] Create `src/retriva/openai_api/routers/chat_completions.py` with `POST /v1/chat/completions`
- [ ] Extract last user message from `messages[]` array
- [ ] Call `ask_question()` and format as OpenAI `ChatCompletion`
- [ ] Build `metadata.citations` from retrieved chunks (source_path, page_title)
- [ ] Populate `usage` with token-count estimates (character-based approximation)
- [ ] API test: verify full response structure, citation presence, edge cases (empty messages, system-only)

## Phase 4: App Setup & Entry Point
- [ ] Create `src/retriva/openai_api/main.py` — FastAPI app with CORS and Qdrant lifespan
- [ ] Create `src/retriva/openai_api/__main__.py` — uvicorn entry point on port 8001
- [ ] Create `src/retriva/openai_api/__init__.py`
- [ ] Create `src/retriva/openai_api/routers/__init__.py`
- [ ] Add `openai_api_port` to `config.py`

## Phase 5: Integration Testing
- [ ] End-to-end test: send chat request → verify grounded answer with citations
- [ ] Regression: verify existing ingestion API tests still pass
- [ ] Manual: connect Open WebUI to `http://<host>:8001/v1` and verify conversation flow
