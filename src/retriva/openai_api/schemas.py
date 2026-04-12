# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

"""
Pydantic schemas matching the OpenAI Chat Completions and Models API.

These schemas are the contract between Open WebUI (or any OpenAI-compatible
client) and Retriva.  They intentionally mirror the OpenAI spec — field names,
types, and nesting must not diverge.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
import time
import uuid


# ---------------------------------------------------------------------------
# Citation metadata (Retriva extension, nested inside messages)
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    document_id: str = Field(..., description="Source path or canonical document ID")
    title: str = Field("", description="Page title from chunk metadata")
    source: str = Field("", description="Source URL or filesystem path")


class MessageMetadata(BaseModel):
    citations: List[Citation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Chat messages
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str = Field(..., description="One of: system, user, assistant")
    content: str = Field(..., description="Message text")
    metadata: Optional[MessageMetadata] = None


# ---------------------------------------------------------------------------
# Chat completions — request
# ---------------------------------------------------------------------------

class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model identifier (accepted but ignored)")
    messages: List[ChatMessage] = Field(..., min_length=1)
    stream: bool = Field(False, description="Accepted but ignored (not yet supported)")
    temperature: Optional[float] = None
    top_p: Optional[float] = None


# ---------------------------------------------------------------------------
# Chat completions — response
# ---------------------------------------------------------------------------

class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = "retriva"
    choices: List[ChatChoice]
    usage: UsageInfo = Field(default_factory=UsageInfo)


# ---------------------------------------------------------------------------
# Chat completions — streaming response (SSE delta protocol)
# ---------------------------------------------------------------------------

class DeltaContent(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class StreamingChoice(BaseModel):
    index: int = 0
    delta: DeltaContent
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = "retriva"
    choices: List[StreamingChoice]


# ---------------------------------------------------------------------------
# Models — response
# ---------------------------------------------------------------------------

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "retriva"


class ListModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]
