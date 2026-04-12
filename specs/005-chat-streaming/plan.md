# Implementation Plan — Chat Streaming

## Phase 1: Streaming Schemas

Add to `src/retriva/openai_api/schemas.py`:
- `DeltaContent(role: Optional[str], content: Optional[str])` — the incremental piece
- `StreamingChoice(index: int, delta: DeltaContent, finish_reason: Optional[str])` — one per chunk
- `ChatCompletionChunk(id, object="chat.completion.chunk", created, model, choices)` — wraps one SSE event

## Phase 2: Streaming Answerer

Add to `src/retriva/qa/answerer.py`:

```python
def ask_question_streaming(question: str, retriever_top_k: int = 5):
    """
    Streaming variant of ask_question().
    Returns (chunks, content_generator) where:
    - chunks: list of retrieved context chunks (for citation building)
    - content_generator: iterator of content strings from the LLM stream
    """
    chunks = retrieve_top_chunks(question, retriever_top_k=retriever_top_k)
    system_prompt = build_prompt(question, chunks)
    
    client = OpenAI(api_key=..., base_url=...)
    stream = client.chat.completions.create(
        model=settings.chat_model,
        messages=[...],
        temperature=settings.chat_temperature,
        top_p=settings.chat_top_p,
        stream=True,
    )
    
    def content_generator():
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    
    return chunks, content_generator()
```

Note: grounding validation is **skipped** in streaming mode (it requires the
full answer text).

## Phase 3: Endpoint Branching

Modify `create_chat_completion()` in `chat_completions.py`:

```python
if request.stream:
    return _handle_streaming(request, question)
else:
    return _handle_non_streaming(request, question)  # existing logic
```

`_handle_streaming()`:
1. Call `ask_question_streaming(question, ...)`
2. Build an async generator that yields SSE lines:
   - First: `data: {ChatCompletionChunk with delta={role: "assistant"}}` 
   - Per content token: `data: {ChatCompletionChunk with delta={content: "..."}}`
   - Last: `data: {ChatCompletionChunk with delta={}, finish_reason="stop"}`
   - Terminal: `data: [DONE]`
3. Return `StreamingResponse(generator, media_type="text/event-stream")`

## Phase 4: Testing

- **Streaming schema test**: `ChatCompletionChunk` serialization
- **SSE test**: mock `ask_question_streaming` → verify SSE event sequence,
  `data:` prefix, `[DONE]` terminator, correct `object` value
- **Regression**: all 10 existing tests pass (non-streaming + ingestion)
- **Manual**: Open WebUI with `stream=true` → tokens appear incrementally
