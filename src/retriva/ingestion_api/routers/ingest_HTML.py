# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import HtmlIngestRequest, IngestResponse
from retriva.ingestion.html_parser import extract_main_content
from retriva.ingestion.chunker import create_chunks
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

def process_html_in_background(payload: HtmlIngestRequest):
    content = extract_main_content(payload.html_content)
    if not content:
        logger.warning(f"Failed to extract content from {payload.source_path}")
        return
        
    doc = ParsedDocument(
        source_path=payload.source_path,
        canonical_doc_id=payload.source_path,
        page_title=payload.page_title,
        content_text=content
    )
    chunks = create_chunks(doc)
    client = get_client()
    upsert_chunks(client, chunks)

@router.post("/html", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_html(payload: HtmlIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing in background HTML document: {payload.source_path}")
    background_tasks.add_task(process_html_in_background, payload)
    return IngestResponse(status="accepted", message="HTML document accepted for processing")
