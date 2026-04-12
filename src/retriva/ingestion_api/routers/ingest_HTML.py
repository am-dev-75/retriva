# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import HtmlIngestRequest, IngestResponse
from retriva.ingestion.html_parser import extract_main_content
from retriva.ingestion.image_parser import extract_images_from_html, enrich_images_with_vlm
from retriva.ingestion.chunker import create_chunks
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.ingestion_api.job_manager import JobManager, CancellationError
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

def process_html_in_background(payload: HtmlIngestRequest, job_id: str):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        images = extract_images_from_html(payload.html_content)

        # Enrich images with VLM descriptions (requires origin file path)
        enrich_images_with_vlm(images, payload.origin_file_path)

        content = extract_main_content(payload.html_content)

        if not content and not images:
            logger.warning(f"Failed to extract content and images from {payload.source_path}")
            manager.complete_job(job_id)
            return

        doc = ParsedDocument(
            source_path=payload.source_path,
            canonical_doc_id=payload.source_path,
            page_title=payload.page_title,
            content_text=content or "",
            images=images
        )
        chunks = create_chunks(doc)
        client = get_client()
        upsert_chunks(client, chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during HTML processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")

@router.post("/html", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_html(payload: HtmlIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing in background HTML document: {payload.source_path}")
    manager = JobManager()
    job = manager.create_job(source=payload.source_path, job_type="html")
    background_tasks.add_task(process_html_in_background, payload, job.id)
    return IngestResponse(status="accepted", message="HTML document accepted for processing", job_id=job.id)
