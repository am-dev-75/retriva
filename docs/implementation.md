# Notes about the implementation

- [Notes about the implementation](#notes-about-the-implementation)
  - [Retrieval](#retrieval)
  - [Exposed APIs](#exposed-apis)
    - [Ingestion API](#ingestion-api)
    - [OpenAI API](#openai-api)
  - [Open WebUI Interfacing](#open-webui-interfacing)
    - [Streaming support](#streaming-support)
    - [Job cancellation support](#job-cancellation-support)
    - [Knowledge Base Management](#knowledge-base-management)

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

### Knowledge Base Management

Retriva maintains its knowledge base in a vector database. For instance, when working in tandem with Qdrant, it makes use of the `retriva_chunks` collection. 

When Retriva is interfaced to Open WebUI, the OWUI adapter maintains a synchronization between OWUI's KBs and Retriva's KB. Associations between OWUI's KBs and Retriva's KB can be viewed by using debugging endpoints exposed by the adapter. For instance:

```
$ curl http://localhost:8002/internal/mappings/knowledge-bases | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   160  100   160    0     0  41862      0 --:--:-- --:--:-- --:--:-- 53333
[
  {
    "owui_kb_id": "749ee4bc-2738-40bd-ab7e-79c6fff76ee3",
    "retriva_kb_id": "749ee4bc-2738-40bd-ab7e-79c6fff76ee3",
    "last_seen_at": "2026-05-03T09:04:12.693998+00:00"
  }
]
```

In practice, when a document belonging the the OWUI's KB having ID `owui_kb_id` is uploaded, its chuncks are stored in Retriva's KB with  ID set to `retriva_kb_id`. A similar approach is used for document metadata:

```
$ curl http://localhost:8002/internal/mappings/documents | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  6038  100  6038    0     0  3432k      0 --:--:-- --:--:-- --:--:-- 5896k
[
  {
    "id": 26,
    "owui_file_id": "453310e5-1a10-4d44-be02-2582dec2de29",
    "filename": "ey-gl-practical-refrence-architecture-for-cra-compliance-11-2025.pdf",
    "content_type": "application/pdf",
    "content_hash": "1082fa9a0c3c8795cef4958842645f2e2bd1e6adc6865a6af9e529b476e061fe",
    "retriva_doc_id": "owui:453310e5-1a10-4d44-be02-2582dec2de29",
    "status": "synced",
    "created_at": "2026-04-30T20:14:14.499267+00:00",
    "updated_at": "2026-04-30T20:14:14.499267+00:00"
  },
...
```