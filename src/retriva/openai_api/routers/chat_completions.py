# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

import json
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from retriva.openai_api.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ChatChoice,
    ChatMessage,
    MessageMetadata,
    Citation,
    UsageInfo,
    DeltaContent,
    StreamingChoice,
)
from retriva.qa.answerer import ask_question, ask_question_streaming
from retriva.config import settings
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _extract_user_question(request: ChatCompletionRequest) -> str:
    """Return the content of the last 'user' message, or raise 400."""
    for msg in reversed(request.messages):
        if msg.role == "user":
            return msg.content
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No message with role 'user' found in the messages array.",
    )


def _build_citations(chunks: list[dict]) -> list[Citation]:
    """Extract citation metadata from retrieved chunk payloads."""
    seen = set()
    citations = []
    for chunk in chunks:
        doc_id = chunk.get("doc_id", chunk.get("source_path", ""))
        if doc_id in seen:
            continue
        seen.add(doc_id)
        citations.append(
            Citation(
                document_id=doc_id,
                title=chunk.get("page_title", ""),
                source=chunk.get("source_path", ""),
            )
        )
    return citations


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Non-streaming handler (existing behaviour, unchanged)
# ---------------------------------------------------------------------------

def _handle_non_streaming(
    request: ChatCompletionRequest, question: str
) -> ChatCompletionResponse:
    try:
        result = ask_question(question, settings.retriever_top_k)
    except Exception as e:
        logger.error(f"QA pipeline error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QA pipeline error: {e}",
        )

    answer = result["answer"]
    chunks = result.get("retrieved_chunks", [])
    citations = _build_citations(chunks)

    # Build the prompt text for token estimation (system + user)
    prompt_text = question
    for msg in request.messages:
        prompt_text += msg.content

    response = ChatCompletionResponse(
        model="retriva",
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=answer,
                    metadata=MessageMetadata(citations=citations),
                ),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(
            prompt_tokens=_estimate_tokens(prompt_text),
            completion_tokens=_estimate_tokens(answer),
            total_tokens=_estimate_tokens(prompt_text) + _estimate_tokens(answer),
        ),
    )

    logger.debug(
        f"Chat completion response — {len(citations)} citation(s), "
        f"{response.usage.total_tokens} est. tokens"
    )
    return response


# ---------------------------------------------------------------------------
# Streaming handler (new — SSE delta protocol)
# ---------------------------------------------------------------------------

def _handle_streaming(
    request: ChatCompletionRequest, question: str
) -> StreamingResponse:
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    try:
        _chunks, content_gen = ask_question_streaming(
            question, settings.retriever_top_k
        )
    except Exception as e:
        logger.error(f"QA pipeline error (streaming init): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QA pipeline error: {e}",
        )

    def _sse_generator():
        # First event: role announcement
        first_chunk = ChatCompletionChunk(
            id=completion_id,
            choices=[
                StreamingChoice(
                    index=0,
                    delta=DeltaContent(role="assistant"),
                    finish_reason=None,
                )
            ],
        )
        yield f"data: {first_chunk.model_dump_json()}\n\n"

        # Content events: one per token
        try:
            for token in content_gen:
                chunk = ChatCompletionChunk(
                    id=completion_id,
                    choices=[
                        StreamingChoice(
                            index=0,
                            delta=DeltaContent(content=token),
                            finish_reason=None,
                        )
                    ],
                )
                yield f"data: {chunk.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"Streaming error mid-flight: {e}")
            # Close the stream gracefully — client will see truncated output

        # Final event: stop signal
        stop_chunk = ChatCompletionChunk(
            id=completion_id,
            choices=[
                StreamingChoice(
                    index=0,
                    delta=DeltaContent(),
                    finish_reason="stop",
                )
            ],
        )
        yield f"data: {stop_chunk.model_dump_json()}\n\n"

        # Terminator
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------

@router.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    When ``stream=false`` (default): returns a single JSON ChatCompletion.
    When ``stream=true``: returns an SSE stream of ChatCompletionChunk events
    following the OpenAI delta protocol.
    """
    question = _extract_user_question(request)
    logger.info(
        f"Chat completion request (stream={request.stream}) — "
        f"question: {question[:120]}..."
    )

    if request.stream:
        return _handle_streaming(request, question)
    else:
        return _handle_non_streaming(request, question)
