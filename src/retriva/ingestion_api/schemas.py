# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from pydantic import BaseModel, Field
from typing import List, Optional
from retriva.domain.models import Chunk

class HtmlIngestRequest(BaseModel):
    source_path: str = Field(..., description="Canonical URL or source path.")
    page_title: str = Field("", description="Title of the page.")
    html_content: str = Field(..., description="Raw HTML content.")

class TextIngestRequest(BaseModel):
    source_path: str = Field(..., description="Canonical URL or source path.")
    page_title: str = Field("", description="Title of the page.")
    content_text: str = Field(..., description="Plain text to chunk.")

class ChunkIngestRequest(BaseModel):
    chunks: List[Chunk] = Field(..., description="List of completely raw Chunk objects.")

class IngestResponse(BaseModel):
    status: str
    message: str
