# Acceptance Criteria — Job Cancellation

## Functional — Job Tracking

- All ingestion endpoints (`/html`, `/text`, `/image`, `/chunks`) return a
  `job_id` in the response
- `GET /api/v1/jobs` returns a list of all tracked jobs with status
- `GET /api/v1/jobs/{job_id}` returns detail for a specific job
- Job status reflects reality: `pending` → `running` → `completed`/`failed`
- Unknown `job_id` returns 404

## Functional — Cancellation

- `POST /api/v1/jobs/{job_id}/cancel` transitions a `running`/`pending` job
  to `cancelling`
- The background worker stops at the next batch boundary and transitions
  to `cancelled`
- `POST /api/v1/jobs/{job_id}/cancel` on a completed job returns 409 Conflict
  (completed jobs cannot be cancelled)
- `POST /api/v1/jobs/{job_id}/cancel` on an already cancelling/cancelled job
  is idempotent (returns 200, no state change)
- Unknown `job_id` returns 404

## Functional — State Machine

- Valid transitions only: pending→running, running→completed, running→failed,
  running→cancelling, pending→cancelling, cancelling→cancelled
- Terminal states (`completed`, `failed`, `cancelled`) cannot transition further

## Non-functional

- Job tracking is **in-memory** (no external database)
- `JobManager` is **thread-safe** (background tasks run in thread pool)
- Existing ingestion tests pass without modification (backward-compatible)
- `IngestResponse.job_id` is optional (existing clients are unaffected)
- No performance regression — cancellation check is O(1) dict lookup
- Chunks already upserted before cancellation remain in Qdrant (no rollback)
