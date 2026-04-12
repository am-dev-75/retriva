# Acceptance Criteria — Chat Streaming

## Functional — Streaming mode (`stream=true`)

- `POST /v1/chat/completions` with `stream=true` returns `Content-Type: text/event-stream`
- Each SSE line is prefixed with `data: ` followed by a JSON object
- The first event contains `delta: {"role": "assistant"}` with no content
- Subsequent events contain `delta: {"content": "..."}` with incremental text
- The final content event has `finish_reason: "stop"` and `delta: {}`
- The stream ends with `data: [DONE]`
- The `object` field in each chunk is `"chat.completion.chunk"` (not `"chat.completion"`)
- All chunks share the same `id` value (e.g., `chatcmpl-xxx`)
- Token output comes from the actual upstream LLM stream (not simulated)

## Functional — Non-streaming preserved (`stream=false`)

- `stream=false` (or omitted) returns the same JSON response as before
- The response `object` remains `"chat.completion"`
- Citation metadata is still present in non-streaming responses
- All existing tests continue to pass without modification

## Non-functional

- Compatible with Open WebUI's streaming renderer
- No new dependencies required
- Retrieval and prompt building remain synchronous (no performance regression)
- Upstream LLM errors during streaming are gracefully handled (stream closes cleanly)
