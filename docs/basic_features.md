# Basic features

The following features are part of Retriva's basic functionality, and are intended to be used in combination with [Open WebUI](https://github.com/open-webui/open-webui) and its adapter for Retriva.

## Internal profiler

The internal profiler is a debugging tool that allows you to see how long each step of the RAG pipeline takes.

To enable it, set the `ENABLE_INTERNAL_PROFILER` environment variable to `true`.

The profiler logs each step to the console.

Example output:

```
...
[20260428 16:05:06] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'request_received' reached at 0.00ms
[20260428 16:05:06] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'request_validated' reached at 0.11ms
[20260428 16:05:07] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'retrieval_vector_search_complete' reached at 825.38ms
[20260428 16:05:07] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'retrieval_ranking_complete' reached at 825.45ms
[20260428 16:05:07] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'prompt_construction_complete' reached at 825.70ms
[20260428 16:05:07] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'inference_request_sent' reached at 844.89ms
[20260428 16:05:17] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'inference_first_token_received' reached at 11147.15ms
[20260428 16:05:26] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'inference_complete' reached at 19817.17ms
[20260428 16:05:26] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'post_processing_complete' reached at 19817.99ms
[20260428 16:05:26] [DEBUG] [Profiler][f880bb28-79b4-4bef-9797-ee5a46b5ec19] Phase 'response_sent' reached at 19818.75ms
...
```
Times are expressed in milliseconds and are relative to the start of the request (`Phase 'request_received'`). When a request/response session completes, the profiler emits a structured log message with all the collected data, which can be read from the endpoint `/internal/profiler/log`. The log message is in JSON format. Example:

```
[20260428 16:05:26] [INFO] PROFILER_LOG: {
  "request_id": "f880bb28-79b4-4bef-9797-ee5a46b5ec19",
  "timestamp": "2026-04-28T14:05:26.252540+00:00",
  "model": "qwen/qwen3.5-27b",
  "provider": "https://openrouter.ai/api/v1",
  "is_streaming": true,
  "phases": {
    "request_received": 0,
    "request_validated": 0.11,
    "retrieval_vector_search_complete": 825.38,
    "retrieval_ranking_complete": 825.45,
    "prompt_construction_complete": 825.7,
    "inference_request_sent": 844.89,
    "inference_first_token_received": 11147.15,
    "inference_complete": 19817.17,
    "post_processing_complete": 19817.99,
    "response_sent": 19818.75
  },
  "total_duration_ms": 19818.81
}
```