# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import ChunkIngestRequest, IngestResponse
from retriva.indexing.qdrant_store import get_client, upsert_chunks, init_collection, COLLECTION_NAME
from retriva.ingestion_api.job_manager import JobManager, CancellationError
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_chunks_in_background(payload: ChunkIngestRequest, job_id: str):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        if not payload.chunks:
            manager.complete_job(job_id)
            return
        client = get_client()
        upsert_chunks(client, payload.chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during chunk processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")


@router.post("/chunks", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_chunks(payload: ChunkIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing in background chunks: {payload.chunks}")
    manager = JobManager()
    job = manager.create_job(source="chunks", job_type="chunks")
    background_tasks.add_task(process_chunks_in_background, payload, job.id)
    return IngestResponse(status="accepted", message="Chunks accepted for processing", job_id=job.id)

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
