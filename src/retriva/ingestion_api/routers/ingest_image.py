# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

import hashlib
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import ImageIngestRequest, IngestResponse
from retriva.domain.models import Chunk, ChunkMetadata
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.ingestion_api.job_manager import JobManager, CancellationError
from retriva.registry import CapabilityRegistry
from retriva.logger import get_logger

# Import module to trigger default registration
import retriva.ingestion.vlm_describer  # noqa: F401 — registers DefaultVLMDescriber

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_image_in_background(payload: ImageIngestRequest, job_id: str):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        logger.debug(f"Processing image in background: {payload.file_path}")

        # Cancellation checkpoint before VLM call (can be slow)
        if cancel_check():
            raise CancellationError("Job cancelled before VLM description")

        image_path = Path(payload.file_path)

        # Call VLM for a detailed description
        registry = CapabilityRegistry()
        vlm = registry.get_instance("vlm_describer")
        description = vlm.describe(image_path)

        text_parts = [f"Image: {image_path.name}"]
        if description:
            logger.debug(f"Image description: {description}")
            text_parts.append(f"Description: {description}")
        else:
            logger.warning(f"VLM returned empty description for {payload.file_path}")
            text_parts.append(f"File: {payload.file_path}")

        text = "\n".join(text_parts)

        chunk_id = hashlib.md5(
            f"{payload.source_path}_img_0".encode("utf-8")
        ).hexdigest()

        meta = ChunkMetadata(
            doc_id=payload.source_path,
            source_path=payload.source_path,
            page_title=payload.page_title,
            section_path="",
            chunk_id=chunk_id,
            chunk_index=0,
            chunk_type="image",
            language="en",
            image_path=payload.file_path,
            user_metadata=payload.user_metadata,
        )

        chunk = Chunk(text=text, metadata=meta)
        client = get_client()
        upsert_chunks(client, [chunk], cancel_check=cancel_check)
        manager.complete_job(job_id)

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during image processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")


@router.post("/image", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_image(payload: ImageIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing standalone image: {payload.file_path}")
    manager = JobManager()
    job = manager.create_job(source=payload.source_path, job_type="image")
    background_tasks.add_task(process_image_in_background, payload, job.id)
    return IngestResponse(status="accepted", message="Image accepted for processing", job_id=job.id)
