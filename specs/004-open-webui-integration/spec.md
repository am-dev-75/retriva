# Feature Spec — 004 Open WebUI Integration

## Goal

Expose Retriva as a **remote RAG backend** fully compatible with **Open WebUI**
via the OpenAI Chat Completions API. Open WebUI connects to Retriva as an
external OpenAI-compatible endpoint — no custom adapters, plugins, or native
functions are required.

## Background

Retriva currently has:
- An **internal QA pipeline** (`qa/answerer.py`) that retrieves context from
  Qdrant, builds a grounded prompt, calls an LLM, and validates grounding
- A **Streamlit UI** (`ui/streamlit_app.py`) that calls the QA pipeline directly
- A **Modular Injection API** (`ingestion_api/`) for document ingestion

There is **no HTTP-facing chat endpoint**. Open WebUI requires one at
`/v1/chat/completions` following the OpenAI schema.

## In scope

### Chat completions (`/v1/chat/completions`)
- OpenAI-compatible request schema (`model`, `messages`, optional `stream`)
- OpenAI-compatible response schema (`id`, `object`, `choices`, `usage`)
- Under the hood: extract user question from messages → run existing
  `ask_question()` pipeline → format as OpenAI response
- **Non-streaming** (synchronous) — the endpoint blocks until the LLM responds

### Model listing (`/v1/models`)
- Required by Open WebUI for connection validation and model selection
- Returns a list with one entry: `retriva` (the system acts as a single unified
  model wrapping retrieval + generation)

### Citation metadata (best-effort)
- Embed source URLs and titles in the response text using `[Document N]`
  notation (already done by the prompt template)
- Include structured citation metadata in an extra `metadata.citations` field
  on the response message — Open WebUI may not render this natively (it
  requires native Tools/Functions), but it's useful for API consumers and
  future compatibility

## Out of scope

- **Streaming** (`stream: true`) — deferred to a future version
- **Authentication / RBAC** — no API key validation on Retriva's side
- **Knowledge base management APIs** — Open WebUI does not have a standard
  protocol for KB CRUD via OpenAI-compatible endpoints; ingestion remains
  through the existing `/api/v1/ingest/*` endpoints
- **Hybrid retrieval** (keyword + vector)
- **Multi-collection routing** — all queries go to the single
  `retriva_chunks` collection
- **Native Open WebUI Tools/Functions** — would require running inside Open
  WebUI's process, which violates "treat Open WebUI as an external client"

## Constraints (from AGENTS.md & constitution)

- `/v1/chat/completions` **MUST** be OpenAI-compatible
- Open WebUI is treated as an **external client** — no coupling
- Existing ingestion and retrieval logic must be preserved
- The main repository `README.md` must not be modified

## Acceptance summary

Open WebUI can be configured to connect to Retriva's `/v1/chat/completions`
endpoint, select the `retriva` model, send questions, and receive grounded
answers with `[Document N]` citations visible in the chat.
