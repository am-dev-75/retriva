# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from pydantic import BaseModel, Field
from typing import List, Optional
from retriva.domain.models import Chunk

class HtmlIngestRequest(BaseModel):
    source_path: str = Field(..., description="Canonical URL or source path.")
    page_title: str = Field("", description="Title of the page.")
    html_content: str = Field(..., description="Raw HTML content.")
    origin_file_path: str = Field("", description="Original filesystem path of the HTML file (for resolving relative image paths).")

class TextIngestRequest(BaseModel):
    source_path: str = Field(..., description="Canonical URL or source path.")
    page_title: str = Field("", description="Title of the page.")
    content_text: str = Field(..., description="Plain text to chunk.")

class ImageIngestRequest(BaseModel):
    source_path: str = Field(..., description="Canonical URL or source path.")
    page_title: str = Field("", description="Title of the page.")
    file_path: str = Field(..., description="Absolute path to the image file on disk.")

class MediaWikiIngestRequest(BaseModel):
    source_path: str = Field(..., description="Path to the source XML export file.")
    page_title: str = Field(..., description="MediaWiki page title.")
    content_text: str = Field(..., description="Plain text extracted from wikitext.")
    page_id: int = Field(0, description="MediaWiki page ID.")
    namespace: int = Field(0, description="MediaWiki namespace number.")
    linked_assets: List[str] = Field(default_factory=list, description="Resolved local asset paths.")

class PdfIngestRequest(BaseModel):
    source_path: str = Field(..., description="Absolute path to the PDF file.")
    page_title: str = Field(..., description="Derived document title.")
    content_text: str = Field(..., description="Plain text from one PDF page.")
    page_number: int = Field(..., description="1-indexed page number.")
    total_pages: int = Field(0, description="Total pages in the PDF.")

class ChunkIngestRequest(BaseModel):
    chunks: List[Chunk] = Field(..., description="List of completely raw Chunk objects.")

class IngestResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    source: str
    job_type: str
    created_at: str
    updated_at: str
    error: Optional[str] = None
