# Feature Spec — 005 Chat Streaming

## Goal

Add **OpenAI-compatible streaming** support to `POST /v1/chat/completions`.
When `stream=true`, the endpoint returns an SSE (Server-Sent Events) stream
using the OpenAI **delta protocol** — each event contains an incremental
fragment of the assistant's response rather than the full message.

## Background

Retriva already has a working non-streaming chat completions endpoint (spec
004). It calls `ask_question()` which:
1. Retrieves context chunks from Qdrant
2. Builds a grounded system prompt
3. Calls the upstream LLM (via OpenAI SDK) as a blocking request
4. Validates grounding

For streaming, steps 1–2 (retrieval + prompt building) remain synchronous.
Only step 3 (LLM generation) is streamed — the OpenAI Python SDK natively
supports `stream=True` and returns an iterator of delta chunks.

## In scope

- When `stream=true` in the request:
  - Return `Content-Type: text/event-stream`
  - First SSE event: `data: {..., "choices": [{"delta": {"role": "assistant"}, ...}]}`
  - Subsequent events: `data: {..., "choices": [{"delta": {"content": "..."}, ...}]}`
  - Final event: `data: [DONE]`
  - `object` field is `"chat.completion.chunk"` (not `"chat.completion"`)
- When `stream=false` (or omitted): existing non-streaming behavior unchanged
- The upstream LLM call uses `stream=True` on the OpenAI SDK to get real
  token-by-token output (not simulated chunking of a complete response)

## Out of scope

- Tool streaming / function calling
- `stream_options.include_usage` (usage stats in streaming mode)
- Grounding validation on streamed responses (would require buffering the
  full answer, defeating the purpose of streaming)
- Citation metadata in streaming deltas (citations require the full answer;
  they remain available only in non-streaming mode)

## Constraints (from AGENTS.md)

- **Preserve non-streaming behavior** — `stream=false` must be identical
- **OpenAI SSE delta protocol** — exact format, not a custom variant
- **Do not modify repository README.md**

## Acceptance summary

Open WebUI can send `stream=true` and see the assistant's response appear
token-by-token in the chat interface, matching the behavior of native OpenAI
streaming.
