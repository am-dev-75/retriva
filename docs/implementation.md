# Notes about the implementation

- [Notes about the implementation](#notes-about-the-implementation)
  - [Retrieval](#retrieval)
  - [Exposed APIs](#exposed-apis)
    - [Ingestion API](#ingestion-api)
    - [OpenAI API](#openai-api)
  - [Open WebUI Interfacing](#open-webui-interfacing)
    - [Streaming support](#streaming-support)
    - [Job cancellation support](#job-cancellation-support)

## Retrieval

The hybrid retrieval feature merges the top ranked vector search results with the top re-ranked results, allowing you to get the best of both worlds: implicit evidence from vector search (when you ask about something you haven't explicitly named) and the accuracy of re-ranking for explicit queries.

The flow looks like this:

vector search → re-ranking → hybrid selection → prompt build

where hybrid selection implies

top M reranked → append up to L vector chunks (deduped).

A two-knob model approach is used, giving precise control:


| Knob                       | Controls                                     | Example |
| -------------------------- | -------------------------------------------- | ------- |
| `HYBRID_RERANK_KEEP_TOP_M` | How many reranked chunks to keep (precision) | 6       |
| `HYBRID_VECTOR_KEEP_TOP_L` | How many vector chunks to add (recall)       | 10      |

This example means you can rerank a broader set (`RETRIEVAL_RERANK_TOP_N = 30`) but only keep the top 6 in the hybrid context, supplemented by 10 vector recall chunks. The `M` knob decouples reranker breadth from the final context composition.

Qdrant (200) → Candidates (20) → Rerank (top 6) → Hybrid (M=6 + L=10) → Budget (25) → LLM
                                       6 chunks   →   up to 16 chunks   →  ≤ 25 sources


## Exposed APIs

Retriva exposes two APIs: an ingestion API and an OpenAI-compatible API.

### Ingestion API

The ingestion API is a proprietary REST API that is used to ingest documents into Retriva. It is located at `/api/v1/ingest` and is mainly used by

* Retriva CLI
* Open WebUI adapter.
  By default it runs on port 8000.

### OpenAI API

The OpenAI-compatible API is located at `/api/v1/chat/completions`. It allows any OpenAI-compatible client to provide questions for Retriva to answer. The answer is streamed back to the client, along with metadata about the answer. For instance [Open WebUI](https://github.com/open-webui/open-webui).

Key design decision: the OpenAI-compatible API lives in a separate package (openai_api/) running by default on port 8001, keeping it cleanly decoupled from the ingestion API.

## Open WebUI Interfacing

For interfacing Retriva with Open WebUI, [an auxiliary service](https://github.com/am-dev-75/open-webui_retriva-adapter) is required. This service allows to ingest new documents into Retriva's knowledge base by uploading them to Open WebUI's chats.

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
