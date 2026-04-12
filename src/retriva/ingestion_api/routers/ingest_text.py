# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import TextIngestRequest, IngestResponse
from retriva.ingestion.chunker import create_chunks
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_text_in_background(payload: TextIngestRequest):
    logger.debug(f"Processing text document in background: {payload.source_path}")

    if not payload.content_text.strip():
        logger.warning(f"Empty text content for {payload.source_path} — skipping.")
        return

    doc = ParsedDocument(
        source_path=payload.source_path,
        canonical_doc_id=payload.source_path,
        page_title=payload.page_title,
        content_text=payload.content_text,
        images=[],
    )
    chunks = create_chunks(doc)
    client = get_client()
    upsert_chunks(client, chunks)


@router.post("/text", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_text(payload: TextIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing text document: {payload.source_path}")
    background_tasks.add_task(process_text_in_background, payload)
    return IngestResponse(status="accepted", message="Text document accepted for processing")
