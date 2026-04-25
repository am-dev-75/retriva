# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

"""
Ingestion endpoint for MediaWiki XML export pages.

Receives pre-parsed plain text (wikitext already converted) and
linked asset paths from the CLI, then chunks, embeds, and indexes
exactly like the text/HTML endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import MediaWikiIngestRequest, IngestResponse
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.ingestion_api.job_manager import JobManager, CancellationError
from retriva.registry import CapabilityRegistry
from retriva.logger import get_logger

# Import module to trigger default registration
import retriva.ingestion.chunker  # noqa: F401 — registers DefaultChunker

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_mediawiki_in_background(payload: MediaWikiIngestRequest, job_id: str):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        logger.debug(
            f"Processing MediaWiki page in background: "
            f"{payload.page_title} (ns={payload.namespace})"
        )

        if not payload.content_text.strip():
            logger.warning(
                f"Empty content for MediaWiki page '{payload.page_title}' — skipping."
            )
            manager.complete_job(job_id)
            return

        doc_id = f"{payload.source_path}#{payload.page_id}"
        doc = ParsedDocument(
            source_path=payload.source_path,
            canonical_doc_id=doc_id,
            page_title=payload.page_title,
            content_text=payload.content_text,
            images=[],
            user_metadata=payload.user_metadata,
        )

        registry = CapabilityRegistry()
        chunks = registry.get_instance("chunker").create_chunks(doc)

        client = get_client()
        upsert_chunks(client, chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)

        logger.info(
            f"MediaWiki page '{payload.page_title}' indexed — "
            f"{len(chunks)} chunk(s)"
        )

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during MediaWiki processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")


@router.post(
    "/mediawiki",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_mediawiki(
    payload: MediaWikiIngestRequest,
    background_tasks: BackgroundTasks,
):
    """Ingest a single MediaWiki page (pre-parsed plain text)."""
    logger.debug(
        f"Received MediaWiki page: {payload.page_title} "
        f"(ns={payload.namespace}, assets={len(payload.linked_assets)})"
    )
    manager = JobManager()
    job = manager.create_job(source=payload.source_path, job_type="mediawiki")
    background_tasks.add_task(process_mediawiki_in_background, payload, job.id)
    return IngestResponse(
        status="accepted",
        message=f"MediaWiki page '{payload.page_title}' accepted for processing",
        job_id=job.id,
    )
