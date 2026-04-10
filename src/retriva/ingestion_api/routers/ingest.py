# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import TextIngestRequest, ChunkIngestRequest, IngestResponse
from retriva.ingestion.chunker import create_chunks
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks, init_collection, COLLECTION_NAME
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])



def process_text_in_background(payload: TextIngestRequest):
    if not payload.content_text:
        return
        
    doc = ParsedDocument(
        source_path=payload.source_path,
        canonical_doc_id=payload.source_path,
        page_title=payload.page_title,
        content_text=payload.content_text
    )
    chunks = create_chunks(doc)
    client = get_client()
    upsert_chunks(client, chunks)

def process_chunks_in_background(payload: ChunkIngestRequest):
    if not payload.chunks:
        return
    client = get_client()
    upsert_chunks(client, payload.chunks)



@router.post("/text", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_text(payload: TextIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing in background text document: {payload.source_path}")
    background_tasks.add_task(process_text_in_background, payload)
    return IngestResponse(status="accepted", message="Text document accepted for processing")

@router.post("/chunks", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_chunks(payload: ChunkIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing in background chunks: {payload.chunks}")
    background_tasks.add_task(process_chunks_in_background, payload)
    return IngestResponse(status="accepted", message="Chunks accepted for processing")

@router.delete("/collection", response_model=IngestResponse, status_code=status.HTTP_200_OK)
async def clear_collection():
    logger.debug("Clearing collection...")
    client = get_client()
    try:
        if client.collection_exists(COLLECTION_NAME):
            client.delete_collection(COLLECTION_NAME)
        init_collection(client)
        return IngestResponse(status="ok", message="Collection cleared and re-initialized")
    except Exception as e:
        logger.error(f"Error clearing collection: {e}")
        return IngestResponse(status="error", message=str(e))
