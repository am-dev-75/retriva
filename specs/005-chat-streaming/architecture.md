# Architecture — Chat Streaming

## Design principle

Streaming is implemented as a **branch in the existing chat completions
endpoint**, not a separate route. When `stream=true`, the endpoint returns a
`StreamingResponse` instead of a JSON response. Retrieval and prompt
construction remain synchronous — only the LLM generation is streamed.

## Request flow

```
Client (Open WebUI)                     Retriva
───────────────────                     ───────
POST /v1/chat/completions
  {stream: true}
                                ┌─ _extract_user_question()
                                ├─ retrieve_top_chunks()      ──►  Qdrant
                                ├─ build_prompt()
                                │
                                │  ┌── OpenAI SDK stream=True ──► LLM
                                │  │
  ◄── SSE: {delta: {role}}      │  │
  ◄── SSE: {delta: {content}}   │  ├── yield chunk
  ◄── SSE: {delta: {content}}   │  ├── yield chunk
  ...                           │  ├── ...
  ◄── SSE: data: [DONE]        │  └── done
```

## SSE event format

Each line follows the pattern:

```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234,"model":"retriva","choices":[{"index":0,"delta":{"content":"token"},"finish_reason":null}]}\n\n
```

The first event has `delta: {"role": "assistant"}` (no content).
The last content event has `finish_reason: "stop"` and `delta: {}`.
After the last event: `data: [DONE]\n\n`

## Proposed changes

### `src/retriva/openai_api/schemas.py` [MODIFY]

Add streaming-specific schemas:
- **`DeltaContent`** — `role` (optional), `content` (optional)
- **`StreamingChoice`** — `index`, `delta: DeltaContent`, `finish_reason`
- **`ChatCompletionChunk`** — `id`, `object="chat.completion.chunk"`, `created`, `model`, `choices: list[StreamingChoice]`

### `src/retriva/qa/answerer.py` [MODIFY]

Add a new function `ask_question_streaming()` that:
1. Runs retrieval + prompt building (same as `ask_question`)
2. Calls `client.chat.completions.create(stream=True)` on the upstream LLM
3. Returns a generator that yields content strings from the stream

The existing `ask_question()` is **not modified** — `ask_question_streaming()`
is a new sibling function.

### `src/retriva/openai_api/routers/chat_completions.py` [MODIFY]

Modify `create_chat_completion()`:
- If `request.stream` is `True`:
  1. Generate a shared `completion_id`
  2. Call `ask_question_streaming()` to get the content generator
  3. Return a `StreamingResponse` that wraps the generator, formatting each
     content chunk as an SSE event with the `ChatCompletionChunk` schema
  4. After the generator is exhausted, emit `data: [DONE]`
- If `request.stream` is `False`: existing behavior, unchanged

### No changes to

- `qa/retriever.py` — retrieval is always synchronous
- `qa/prompting.py` — prompt building is always synchronous
- `qa/grounding.py` — not called in streaming mode
- `openai_api/routers/models.py` — no streaming concern
- `openai_api/main.py` — no routing changes
