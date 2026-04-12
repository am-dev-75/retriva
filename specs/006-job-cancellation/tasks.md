# Tasks — Job Cancellation

## Phase 1: JobManager Core
- [ ] Create `src/retriva/ingestion_api/job_manager.py` — `Job`, `JobStatus`, `JobManager` singleton
- [ ] Thread-safe job CRUD: create, start, complete, fail, request_cancel, mark_cancelled
- [ ] Unit tests for state machine transitions and thread safety

## Phase 2: Job API Router
- [ ] Create `src/retriva/ingestion_api/routers/jobs.py` — GET list, GET detail, POST cancel
- [ ] Add `JobResponse` schema to `schemas.py`
- [ ] Add optional `job_id` field to `IngestResponse`
- [ ] Register `jobs.router` in `main.py`
- [ ] API tests: list, detail, cancel, 404, 409

## Phase 3: Cancellation Checkpoints
- [ ] Add `cancel_check` callback parameter to `upsert_chunks()`
- [ ] Add `cancel_check` callback parameter to `get_embeddings()`
- [ ] Create `CancellationError` exception class
- [ ] Inject checkpoint between batch loops

## Phase 4: Ingestion Router Integration
- [ ] Modify `process_html_in_background()` — job lifecycle + cancel_check
- [ ] Modify `process_text_in_background()` — job lifecycle + cancel_check
- [ ] Modify `process_image_in_background()` — job lifecycle + cancel_check
- [ ] Modify `process_chunks_in_background()` — job lifecycle + cancel_check
- [ ] Update endpoint handlers to create jobs and pass job_id

## Phase 5: Testing
- [ ] End-to-end: submit job → poll status → verify completed
- [ ] End-to-end: submit job → cancel → verify cancelled
- [ ] Regression: all existing tests pass
