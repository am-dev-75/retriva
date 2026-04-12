# Implementation Plan — Job Cancellation

## Phase 1: JobManager Core

Create `src/retriva/ingestion_api/job_manager.py`:

```python
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"

TERMINAL_STATES = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}

class Job:
    __slots__ = ("id", "status", "source", "job_type",
                 "created_at", "updated_at", "error", "cancel_requested")
    # ... init, to_dict ...

class JobManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        # Singleton pattern
    
    def create_job(self, source, job_type) -> Job
    def start_job(self, job_id)          # pending → running
    def complete_job(self, job_id)       # running → completed
    def fail_job(self, job_id, error)    # running → failed
    def request_cancel(self, job_id)     # pending/running → cancelling
    def mark_cancelled(self, job_id)     # cancelling → cancelled
    def is_cancel_requested(self, job_id) -> bool
    def get_job(self, job_id) -> Job | None
    def list_jobs(self) -> list[Job]
```

Thread safety: all mutations guarded by `self._lock`.

## Phase 2: Job API Router

Create `src/retriva/ingestion_api/routers/jobs.py`:

- `GET /api/v1/jobs` → 200, list of `JobResponse`
- `GET /api/v1/jobs/{job_id}` → 200 or 404
- `POST /api/v1/jobs/{job_id}/cancel`:
  - Job in `running`/`pending` → 202 Accepted, state → `cancelling`
  - Job in `cancelling`/`cancelled` → 200 OK (idempotent)
  - Job in `completed`/`failed` → 409 Conflict
  - Unknown job → 404

Add to `schemas.py`:
```python
class JobResponse(BaseModel):
    job_id: str
    status: str
    source: str
    job_type: str
    created_at: str
    updated_at: str
    error: Optional[str] = None

class IngestResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[str] = None  # additive, backward-compatible
```

Register in `main.py`: `app.include_router(jobs.router)`

## Phase 3: Cancellation Checkpoints

Create `CancellationError` (derives from `Exception`) — raised when a
checkpoint detects cancellation, caught by the background worker.

Modify `upsert_chunks()` — add optional `cancel_check: Callable[[], bool] = None`:
```python
for i in range(0, len(chunks), batch_size):
    if cancel_check and cancel_check():
        raise CancellationError("Job cancelled during upsert")
    # ... existing batch logic ...
```

Modify `get_embeddings()` — same pattern:
```python
for i in range(0, len(texts), batch_size):
    if cancel_check and cancel_check():
        raise CancellationError("Job cancelled during embedding")
    # ... existing batch logic ...
```

## Phase 4: Ingestion Router Integration

Each `process_*_in_background()` gains a `job_id` parameter and wraps work:
```python
def process_html_in_background(payload, job_id):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)
    try:
        # ... existing logic ...
        upsert_chunks(client, chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)
    except CancellationError:
        manager.mark_cancelled(job_id)
    except Exception as e:
        manager.fail_job(job_id, str(e))
```

Each endpoint handler creates a job before adding the background task:
```python
@router.post("/html", ...)
async def ingest_html(payload, background_tasks):
    manager = JobManager()
    job = manager.create_job(source=payload.source_path, job_type="html")
    background_tasks.add_task(process_html_in_background, payload, job.id)
    return IngestResponse(status="accepted", message="...", job_id=job.id)
```

## Phase 5: Testing

- **JobManager unit tests** (`tests/test_job_manager.py`):
  - State transitions: create→start→complete, create→start→fail
  - Cancellation: start→request_cancel→mark_cancelled
  - Completed job cannot be cancelled (raises)
  - Thread safety: concurrent creates from multiple threads
- **Jobs API tests** (`tests/test_jobs_api.py`):
  - GET /api/v1/jobs → 200
  - GET /api/v1/jobs/{id} → 200/404
  - POST cancel → 202/409/404
- **Integration test**: submit ingestion → poll job → verify completed
- **Regression**: all 13 existing tests pass (OpenAI + ingestion)
