# Agent Instructions — Retriva Job Cancellation

## Mission
Add **job cancellation** support for asynchronous ingestion jobs.

## Order of authority
1. `specs/006-job-cancellation/spec.md`
2. `specs/006-job-cancellation/openapi.yaml`
3. `.agent/rules/retriva-constitution.md`

## Non-negotiable rules
- Do not modify repository README.md
- Cancellation must be cooperative and safe
- Completed jobs cannot be cancelled
