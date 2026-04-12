# Architecture — Open WebUI Integration

## Design principle

Retriva acts as a **thin OpenAI-compatible facade** over the existing QA
pipeline. Open WebUI connects to it exactly like it connects to OpenAI or any
other compatible backend — no Retriva-specific configuration is needed on the
Open WebUI side beyond the base URL.

## Request flow

```
Open WebUI                       Retriva
─────────                       ───────
  POST /v1/chat/completions  ──►  ChatCompletionsRouter
                                    │
                                    ├──  Extract user question from messages[]
                                    │
                                    ├──  ask_question(question, top_k)
                                    │       ├── retrieve_top_chunks()  ──►  Qdrant
                                    │       ├── build_prompt()
                                    │       ├── LLM call (OpenRouter)
                                    │       └── validate_grounding()
                                    │
                                    ├──  Format as OpenAI ChatCompletion
                                    │       ├── choices[0].message.content = answer
                                    │       └── choices[0].message.metadata.citations = [...]
                                    │
                                    └──►  Return JSON response

  GET /v1/models             ──►  ModelsRouter
                                    └──►  Return [{ id: "retriva", ... }]
```

## Proposed components

### `src/retriva/openai_api/` [NEW package]

A separate FastAPI app dedicated to the OpenAI-compatible interface, keeping it
cleanly separated from the ingestion API (`ingestion_api/`).

#### `src/retriva/openai_api/main.py` [NEW]

FastAPI app with CORS enabled (Open WebUI may run on a different origin):
- Registers `chat_completions.router` and `models.router`
- Lifespan: initializes Qdrant client connection

#### `src/retriva/openai_api/routers/chat_completions.py` [NEW]

Single endpoint:
- `POST /v1/chat/completions`
- Extracts the last `user` message from the `messages` array
- Calls `ask_question()` from the existing QA pipeline
- Formats the result as an OpenAI `ChatCompletion` response
- Includes citation metadata extracted from grounding validation

#### `src/retriva/openai_api/routers/models.py` [NEW]

Single endpoint:
- `GET /v1/models`
- Returns a fixed list with one model: `retriva`
- Follows the OpenAI `ListModelsResponse` schema

#### `src/retriva/openai_api/schemas.py` [NEW]

Pydantic models matching the OpenAI API:
- `ChatCompletionRequest` — `model`, `messages[]`, `stream` (ignored), `temperature`, `top_p`
- `ChatMessage` — `role`, `content`, optional `metadata`
- `ChatCompletionResponse` — `id`, `object`, `created`, `model`, `choices[]`, `usage`
- `ChatChoice` — `index`, `message`, `finish_reason`
- `ModelInfo` / `ListModelsResponse`

#### `src/retriva/openai_api/__main__.py` [NEW]

Entry point: `python -m retriva.openai_api` — runs uvicorn on a configurable
port (default 8001), separate from the ingestion API (8000).

### Configuration changes

#### `src/retriva/config.py` [MODIFY]

Add `openai_api_port: int = 8001` for the chat API server port.

### No changes to existing modules

The existing QA pipeline (`qa/answerer.py`, `qa/retriever.py`,
`qa/prompting.py`, `qa/grounding.py`) is used **as-is**. The OpenAI API layer
is a pure adapter — no modifications to retrieval, prompting, or grounding
logic.
