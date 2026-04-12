# Tasks — Chat Streaming

## Phase 1: Streaming Schemas
- [ ] Add `DeltaContent`, `StreamingChoice`, `ChatCompletionChunk` to `schemas.py`

## Phase 2: Streaming Answerer
- [ ] Add `ask_question_streaming(question, retriever_top_k)` to `answerer.py`
- [ ] Reuse retrieval + prompt building from `ask_question()`
- [ ] Call upstream LLM with `stream=True` via OpenAI SDK
- [ ] Return a generator yielding content strings

## Phase 3: Endpoint Branching
- [ ] Detect `stream=true` in `create_chat_completion()`
- [ ] Build SSE event generator formatting each chunk as `ChatCompletionChunk`
- [ ] First event: role-only delta
- [ ] Content events: content deltas
- [ ] Final event: `finish_reason: "stop"`, empty delta
- [ ] Terminal event: `data: [DONE]`
- [ ] Return `StreamingResponse(media_type="text/event-stream")`
- [ ] Preserve non-streaming path unchanged

## Phase 4: Testing
- [ ] Unit test: streaming schemas serialize correctly
- [ ] API test: `stream=true` returns SSE with correct event sequence
- [ ] API test: `stream=false` behavior unchanged (regression)
- [ ] All existing tests pass without modification
