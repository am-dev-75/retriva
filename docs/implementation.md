# Notes about the implementation

- [Notes about the implementation](#notes-about-the-implementation)
  - [Open WebUI Interfacing](#open-webui-interfacing)
    - [Streaming support](#streaming-support)
    - [Job cancellation support](#job-cancellation-support)

## Open WebUI Interfacing

The implementation was made to allow Open WebUI to interface with Retriva. This was done by creating a new API endpoint that can be called by Open WebUI. The new API endpoint is located at `/api/v1/chat/completions` and is a drop-in replacement for the OpenAI API endpoint. Antigravity + Claude Opus 4.6 was used by following a SDD approach.

Key design decision: the OpenAI-compatible API lives in a separate package (openai_api/) running on port 8001, keeping it cleanly decoupled from the ingestion API on port 8000. It's a pure adapter over the existing ask_question() pipeline — no QA code is modified..

### Streaming support

Key design decisions:

* Branch in existing endpoint, not a new route — `stream=true` triggers StreamingResponse
* Real LLM streaming via `client.chat.completions.create(stream=True)` — tokens arrive from the upstream model
* Grounding validation skipped in streaming mode (it needs the full answer text)
* Citations only in non-streaming — delta protocol has no slot for metadata
* New `ask_question_streaming()` is a sibling of `ask_question()`, not a modification

### Job cancellation support

Key design decisions:

* Cooperative cancellation via `cancel_check` callback injected into `upsert_chunks()` and `get_embeddings()` — checked at batch boundaries
* Thread-safe singleton `JobManager` with `threading.Lock` — `BackgroundTasks` run in a thread pool
* Backward-compatible — `IngestResponse.job_id` is optional; existing clients unaffected
* No rollback — chunks upserted before cancellation stay in Qdrant
* `CancellationError` propagates from checkpoints → caught by the background worker → sets state to cancelled