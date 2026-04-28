# SDD Pack — Internal Request Profiler for Retriva

## Status
Proposed

## Scope
Retriva Core (Thin Adapter and Open WebUI unchanged)

## Summary
This SDD introduces a lightweight, internal request profiler for Retriva to measure end-to-end latency across major processing phases, with special emphasis on remote inference. Profiling data is exposed via structured logs and a gated internal endpoint.

## Motivation
Retriva often relies on remote LLM providers (e.g. via OpenRouter). Without phase-level timing, it is impossible to determine whether latency originates from retrieval, prompt construction, or inference. This profiler provides deterministic observability with minimal overhead.

## Architectural Principles
- Provider-agnostic
- Low overhead (timestamp-based)
- Request-scoped
- Disabled by default
- Internal-only observability

## Profiling Phases
1. request_received
2. request_validated
3. retrieval_vector_search_complete
4. retrieval_ranking_complete
5. prompt_construction_complete
6. inference_request_sent
7. inference_first_token_received (if streaming)
8. inference_complete
9. post_processing_complete
10. response_sent

## Functional Requirements
- A profiler instance is created per request
- Monotonic clocks must be used
- No provider-specific instrumentation
- Streaming-aware inference profiling

## Structured Log Output
Each request emits a structured log entry with ordered phase durations (ms), request id, model, and provider.

## Internal Endpoint
GET /internal/profiler/log

- Read-only
- Returns recent profiler log entries
- Available only when ENABLE_INTERNAL_PROFILER=true
- Returns 404 when disabled

## Configuration
ENABLE_INTERNAL_PROFILER=false (default)

## Security
- Internal endpoint only
- No prompts or document contents exposed

## Non-Goals
- No distributed tracing
- No performance optimization logic
- No UI exposure

## Acceptance Criteria
- Phase timings are correctly measured
- Inference latency is isolated
- Endpoint is gated and read-only
- No behavior change when disabled

## One-Sentence Summary
Retriva gains a lightweight, provider-agnostic internal profiler that records phase-level request timings and exposes them through a gated internal endpoint for diagnostics.