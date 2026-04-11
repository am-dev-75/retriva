# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

import hashlib
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, status
from retriva.ingestion_api.schemas import ImageIngestRequest, IngestResponse
from retriva.ingestion.vlm_describer import describe_image
from retriva.domain.models import Chunk, ChunkMetadata
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_image_in_background(payload: ImageIngestRequest):
    logger.debug(f"Processing image in background: {payload.file_path}")
    image_path = Path(payload.file_path)

    # Call VLM for a detailed description
    description = describe_image(image_path)

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
        image_path=payload.file_path
    )

    chunk = Chunk(text=text, metadata=meta)
    client = get_client()
    upsert_chunks(client, [chunk])


@router.post("/image", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_image(payload: ImageIngestRequest, background_tasks: BackgroundTasks):
    logger.debug(f"Processing standalone image: {payload.file_path}")
    background_tasks.add_task(process_image_in_background, payload)
    return IngestResponse(status="accepted", message="Image accepted for processing")
