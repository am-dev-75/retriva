# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import TextIngestRequest, IngestResponse
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.ingestion_api.job_manager import JobManager, CancellationError
from retriva.registry import CapabilityRegistry
from retriva.logger import get_logger

# Import module to trigger default registration
import retriva.ingestion.chunker  # noqa: F401 — registers DefaultChunker

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_text_in_background(payload: TextIngestRequest, job_id: str):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        logger.debug(f"Processing text document in background: {payload.source_path}")

        if not payload.content_text.strip():
            logger.warning(f"Empty text content for {payload.source_path} — skipping.")
            manager.complete_job(job_id)
            return

        doc = ParsedDocument(
            source_path=payload.source_path,
            canonical_doc_id=payload.source_path,
            page_title=payload.page_title,
            content_text=payload.content_text,
            images=[],
            user_metadata=payload.user_metadata,
        )
        chunks = CapabilityRegistry().get_instance("chunker").create_chunks(doc)
        client = get_client()
        upsert_chunks(client, chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during text processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")


@router.post("/text", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_text(payload: TextIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing text document: {payload.source_path}")
    manager = JobManager()
    job = manager.create_job(source=payload.source_path, job_type="text")
    background_tasks.add_task(process_text_in_background, payload, job.id)
    return IngestResponse(status="accepted", message="Text document accepted for processing", job_id=job.id)
