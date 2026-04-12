# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, HTTPException, status
from retriva.openai_api.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatChoice,
    ChatMessage,
    MessageMetadata,
    Citation,
    UsageInfo,
)
from retriva.qa.answerer import ask_question
from retriva.config import settings
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])


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


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Extracts the user question from the messages array, runs it through
    the full Retriva QA pipeline (retrieve → prompt → LLM → grounding),
    and returns the answer formatted as an OpenAI ChatCompletion.
    """
    question = _extract_user_question(request)
    logger.info(f"Chat completion request — question: {question[:120]}...")

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
