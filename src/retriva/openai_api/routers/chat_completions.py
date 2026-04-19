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
    CitationRef,
    ToolCall,
    ToolCallFunction,
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
                language=chunk.get("language", "en")
            )
        )
    return citations


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token."""
    return max(1, len(text) // 4)


def _build_citation_refs(answer: str, citations: list[Citation]) -> tuple[str, str, list[CitationRef], list[ToolCall]]:
    """
    Parse [Title] markers from the answer, map the preceding sentence to a CitationRef.
    Returns (clean_text, compat_text, citation_refs, tool_calls).
    """
    import re
    title_to_idx = {c.title: i for i, c in enumerate(citations) if c.title}
    
    # Regex to find [Title]
    pattern = r'\[([^\]]+)\]'
    
    clean_text = ""
    compat_text = ""
    citation_refs = []
    
    last_end = 0
    current_clean_index = 0
    
    for match in re.finditer(pattern, answer):
        title = match.group(1)
        if title in title_to_idx:
            citation_idx = title_to_idx[title]
            
            text_segment = answer[last_end:match.start()]
            clean_text += text_segment
            compat_text += text_segment
            
            end_index = current_clean_index + len(text_segment)
            start_index = current_clean_index
            
            # Try to find the start of the sentence
            sentence_start = text_segment.rfind('.')
            if sentence_start != -1:
                start_index = current_clean_index + sentence_start + 1
            else:
                nl_start = text_segment.rfind('\n')
                if nl_start != -1:
                    start_index = current_clean_index + nl_start + 1
            
            # Strip leading whitespace
            while start_index < end_index and clean_text[start_index].isspace():
                start_index += 1
                
            citation_refs.append(
                CitationRef(
                    start_index=max(0, start_index),
                    end_index=end_index,
                    citation_index=citation_idx
                )
            )
            
            compat_text += f"[{citation_idx + 1}]"
            
            current_clean_index = end_index
            last_end = match.end()
        else:
            # Not a known citation, leave it in the text
            text_segment = answer[last_end:match.end()]
            clean_text += text_segment
            compat_text += text_segment
            current_clean_index += len(text_segment)
            last_end = match.end()
            
    clean_text += answer[last_end:]
    compat_text += answer[last_end:]
    
    tool_calls = []
    if citations:
        tool_calls.append(
            ToolCall(
                id=f"call_{uuid.uuid4().hex[:10]}",
                function=ToolCallFunction(
                    name="citation",
                    arguments=json.dumps({"citations": [c.model_dump() for c in citations]})
                )
            )
        )
        
    return clean_text, compat_text, citation_refs, tool_calls


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
    
    clean_text, compat_text, citation_refs, tool_calls = _build_citation_refs(answer, citations)

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
                    content=compat_text,
                    metadata=MessageMetadata(
                        citations=citations,
                        citation_refs=citation_refs,
                        output_text=clean_text
                    ),
                    tool_calls=tool_calls if tool_calls else None
                ),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(
            prompt_tokens=_estimate_tokens(prompt_text),
            completion_tokens=_estimate_tokens(compat_text),
            total_tokens=_estimate_tokens(prompt_text) + _estimate_tokens(compat_text),
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
        yield f"data: {first_chunk.model_dump_json(exclude_none=True)}\n\n"

        citations = _build_citations(_chunks) if _chunks else []
        title_to_idx = {c.title: i for i, c in enumerate(citations) if c.title}
        
        buffer = ""
        out_chunk = ""
        inside_bracket = False
        clean_text_so_far = ""
        citation_refs = []

        # Content events: character by character processing
        try:
            for token in content_gen:
                for char in token:
                    if not inside_bracket:
                        if char == '[':
                            inside_bracket = True
                            buffer += char
                        else:
                            out_chunk += char
                            clean_text_so_far += char
                    else:
                        buffer += char
                        if char == ']':
                            inside_bracket = False
                            content = buffer[1:-1]
                            if content in title_to_idx:
                                citation_idx = title_to_idx[content]
                                end_index = len(clean_text_so_far)
                                
                                sentence_start = clean_text_so_far.rfind('.')
                                if sentence_start != -1:
                                    start_index = sentence_start + 1
                                else:
                                    nl_start = clean_text_so_far.rfind('\n')
                                    if nl_start != -1:
                                        start_index = nl_start + 1
                                    else:
                                        start_index = 0
                                        
                                while start_index < end_index and clean_text_so_far[start_index].isspace():
                                    start_index += 1
                                    
                                citation_refs.append(
                                    CitationRef(
                                        start_index=max(0, start_index),
                                        end_index=end_index,
                                        citation_index=citation_idx
                                    )
                                )
                                
                                out_chunk += f"[{citation_idx + 1}]"
                            else:
                                out_chunk += buffer
                                clean_text_so_far += buffer
                            buffer = ""
                
                if out_chunk:
                    chunk = ChatCompletionChunk(
                        id=completion_id,
                        choices=[
                            StreamingChoice(
                                index=0,
                                delta=DeltaContent(content=out_chunk),
                                finish_reason=None,
                            )
                        ],
                    )
                    yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
                    out_chunk = ""

            if buffer:
                chunk = ChatCompletionChunk(
                    id=completion_id,
                    choices=[
                        StreamingChoice(
                            index=0,
                            delta=DeltaContent(content=buffer),
                            finish_reason=None,
                        )
                    ],
                )
                yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
                clean_text_so_far += buffer
                
        except Exception as e:
            logger.error(f"Streaming error mid-flight: {e}")
            # Close the stream gracefully — client will see truncated output

        # Generate tool calls envelope for streaming at the end
        tool_calls = []
        if _chunks:
            citations = _build_citations(_chunks)
            if citations:
                tool_calls.append(
                    ToolCall(
                        id=f"call_{uuid.uuid4().hex[:10]}",
                        function=ToolCallFunction(
                            name="citation",
                            arguments=json.dumps({"citations": [c.model_dump() for c in citations]})
                        )
                    )
                )

        # Final event: stop signal with tool_calls and metadata
        metadata_payload = MessageMetadata(
            citations=citations,
            citation_refs=citation_refs,
            output_text=clean_text_so_far
        ) if citations else None
        
        stop_chunk = ChatCompletionChunk(
            id=completion_id,
            choices=[
                StreamingChoice(
                    index=0,
                    delta=DeltaContent(
                        tool_calls=tool_calls if tool_calls else None,
                        metadata=metadata_payload
                    ),
                    finish_reason="stop",
                )
            ],
        )
        yield f"data: {stop_chunk.model_dump_json(exclude_none=True)}\n\n"

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
