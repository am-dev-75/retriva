# Feature Spec — 006 Job Cancellation

## Goal

Add **cooperative job cancellation** for asynchronous ingestion jobs.
Users can track job progress and request early termination of long-running
ingestion tasks (HTML parsing, image VLM description, embedding, Qdrant upsert).

## Background

Retriva's ingestion endpoints (`/api/v1/ingest/{html,text,image,chunks}`) use
FastAPI `BackgroundTasks` for fire-and-forget processing. There is currently:
- No way to know if a job is still running, completed, or failed
- No way to cancel a job after submission
- No job identifier returned to the client

Each `process_*_in_background()` function runs a synchronous pipeline:
1. Parse content (HTML extraction, VLM image description)
2. Create chunks (`create_chunks()`)
3. Embed chunks in batches (`get_embeddings()`)
4. Upsert to Qdrant in batches (`upsert_chunks()`)

Steps 3–4 loop over batch boundaries — these are the natural **cancellation
checkpoints** where the job can safely stop without leaving partial state.

## In scope

### Job tracking
- Thread-safe in-memory `JobManager` singleton tracking all ingestion jobs
- Job states: `pending` → `running` → `completed` / `failed` / `cancelling` → `cancelled`
- Each ingestion endpoint returns a `job_id` in the response (additive — backward-compatible)

### Job status API
- `GET /api/v1/jobs` — list all jobs with status
- `GET /api/v1/jobs/{job_id}` — single job detail (status, source, timestamps)

### Job cancellation
- `POST /api/v1/jobs/{job_id}/cancel` — request cooperative cancellation
- Sets job state to `cancelling`
- Background worker checks `job.is_cancel_requested` at batch boundaries
- When cancellation is detected, worker stops processing, sets state to `cancelled`

### Cancellation checkpoints
- Between embedding batches in `get_embeddings()`
- Between Qdrant upsert batches in `upsert_chunks()`
- Before VLM description call in `process_image_in_background()`

## Out of scope

- **Force-kill** of threads/processes — only cooperative cancellation
- **Persistent storage** — jobs are in-memory only (lost on restart)
- **Job queuing / prioritization** — no queue, jobs run immediately
- **Partial rollback** — chunks already upserted before cancellation stay in Qdrant
- **CLI job tracking** — only API consumers see job IDs

## Constraints (from AGENTS.md)

- Cancellation must be **cooperative and safe** — no thread interruption
- **Completed jobs cannot be cancelled**
- **Do not modify repository README.md**
- Existing fire-and-forget behavior must still work (job_id is optional in response)

## Acceptance summary

A user submits an ingestion request, receives a `job_id`, can poll
`GET /api/v1/jobs/{job_id}` to see progress, and can call
`POST /api/v1/jobs/{job_id}/cancel` to stop it. The job transitions to
`cancelled` at the next batch boundary.
