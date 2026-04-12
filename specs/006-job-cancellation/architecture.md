# Architecture — Job Cancellation

## Job state machine

```
                  submit
                    │
                    ▼
               ┌─────────┐
               │ pending  │
               └────┬─────┘
                    │  worker picks up
                    ▼
               ┌─────────┐     cancel request
               │ running  │──────────────────┐
               └────┬─────┘                  │
                    │                        ▼
              ┌─────┴──────┐          ┌────────────┐
              │             │          │ cancelling  │
              ▼             ▼          └─────┬──────┘
        ┌──────────┐  ┌─────────┐            │  checkpoint reached
        │ completed│  │  failed │            ▼
        └──────────┘  └─────────┘     ┌────────────┐
                                      │ cancelled   │
                                      └────────────┘
```

Terminal states: `completed`, `failed`, `cancelled` — no further transitions.

## Proposed components

### `src/retriva/ingestion_api/job_manager.py` [NEW]

Thread-safe singleton managing all job lifecycle:

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"

class Job:
    id: str                    # UUID4
    status: JobStatus
    source: str                # source_path from the ingest request
    job_type: str              # "html", "text", "image", "chunks"
    created_at: datetime
    updated_at: datetime
    error: Optional[str]       # set on failure
    cancel_requested: bool     # flag checked by workers

class JobManager:
    _jobs: dict[str, Job]      # guarded by threading.Lock
    
    def create_job(source, job_type) -> Job
    def get_job(job_id) -> Job | None
    def list_jobs() -> list[Job]
    def start_job(job_id)          # pending → running
    def complete_job(job_id)       # running → completed
    def fail_job(job_id, error)    # running → failed
    def request_cancel(job_id)     # running/pending → cancelling
    def mark_cancelled(job_id)     # cancelling → cancelled
    def is_cancel_requested(job_id) -> bool
```

### `src/retriva/ingestion_api/routers/jobs.py` [NEW]

New router registered on the ingestion API:

- `GET /api/v1/jobs` → list all jobs
- `GET /api/v1/jobs/{job_id}` → single job detail
- `POST /api/v1/jobs/{job_id}/cancel` → request cancellation

### `src/retriva/ingestion_api/schemas.py` [MODIFY]

Add:
- `JobResponse` — status, source, job_type, timestamps, error
- `IngestResponse.job_id: Optional[str]` — backward-compatible addition

### Ingestion routers [MODIFY]

Each `process_*_in_background()` function wraps its work with job lifecycle:

```python
def process_html_in_background(payload, job_id):
    job_manager.start_job(job_id)
    try:
        # ... existing logic ...
        # At batch boundaries:
        if job_manager.is_cancel_requested(job_id):
            job_manager.mark_cancelled(job_id)
            return
        job_manager.complete_job(job_id)
    except Exception as e:
        job_manager.fail_job(job_id, str(e))
```

### Cancellation checkpoints [MODIFY]

#### `src/retriva/indexing/qdrant_store.py`

`upsert_chunks()` accepts an optional `cancel_check` callback. Between batches:
```python
if cancel_check and cancel_check():
    logger.info("Cancellation requested — stopping upsert.")
    raise CancellationError()
```

#### `src/retriva/indexing/embeddings.py`

`get_embeddings()` accepts an optional `cancel_check` callback. Between batches:
```python
if cancel_check and cancel_check():
    logger.info("Cancellation requested — stopping embedding.")
    raise CancellationError()
```

### `src/retriva/ingestion_api/main.py` [MODIFY]

Register `jobs.router`.

### No changes to

- `openai_api/` — chat endpoint has no ingestion concern
- `qa/` — retrieval/answering pipeline
- `domain/models.py` — chunk/document models
