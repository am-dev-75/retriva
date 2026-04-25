# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import MarkdownIngestRequest, IngestResponse
from retriva.domain.models import ParsedDocument, Chunk, ChunkMetadata
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.ingestion_api.job_manager import JobManager, CancellationError
from retriva.registry import CapabilityRegistry
from retriva.logger import get_logger

# Import module to trigger default registration
import retriva.ingestion.chunker  # noqa: F401 — registers DefaultChunker

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_markdown_in_background(payload: MarkdownIngestRequest, job_id: str):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        logger.debug(f"Processing markdown document in background: {payload.source_path}")

        all_chunks = []
        chunker = CapabilityRegistry().get_instance("chunker")

        for i, section in enumerate(payload.sections):
            if not section.content.strip():
                continue

            # Create a virtual document for this section to reuse the chunker
            # We preserve the heading in the section_path metadata
            section_doc = ParsedDocument(
                source_path=payload.source_path,
                canonical_doc_id=payload.source_path,
                page_title=payload.page_title,
                content_text=section.content,
                images=[],
                user_metadata=payload.user_metadata,
            )
            
            section_chunks = chunker.create_chunks(section_doc)
            
            # Enrich chunks with section metadata
            for chunk in section_chunks:
                chunk.metadata.section_path = section.heading
                all_chunks.append(chunk)

        if not all_chunks:
            logger.warning(f"No chunks generated for {payload.source_path} — skipping.")
            manager.complete_job(job_id)
            return

        client = get_client()
        upsert_chunks(client, all_chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during markdown processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")


@router.post("/markdown", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_markdown(payload: MarkdownIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing markdown document: {payload.source_path}")
    manager = JobManager()
    job = manager.create_job(source=payload.source_path, job_type="markdown")
    background_tasks.add_task(process_markdown_in_background, payload, job.id)
    return IngestResponse(status="accepted", message="Markdown document accepted for processing", job_id=job.id)
