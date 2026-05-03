# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
v2 document ingestion endpoints.

Provides a generic, format-agnostic ingestion pipeline that detects
document type and routes to the appropriate parser.  Supports both
JSON-body requests (``source_uri``) and multipart file uploads.
"""

import json as _json
import os
import shutil
import tempfile
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status

from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.ingestion.normalize import normalize_text
from retriva.ingestion_api.job_manager import CancellationError, JobManager
from retriva.ingestion_api.schemas import UserMetadataValidationError, validate_user_metadata
from retriva.ingestion_api.schemas_v2 import (
    DocumentIngestRequestV2,
    IngestResponseV2,
    JobStage,
)
from retriva.logger import get_logger
from retriva.registry import CapabilityRegistry

# Import module to trigger default registrations
import retriva.ingestion.chunker        # noqa: F401 — registers DefaultChunker
import retriva.ingestion.parser_router  # noqa: F401 — registers DefaultParserRouter

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v2/documents", tags=["v2-documents"])


# ---------------------------------------------------------------------------
# Shared background worker
# ---------------------------------------------------------------------------

def process_document_v2(
    source_uri: str,
    content_type: Optional[str],
    user_metadata: Optional[Dict[str, str]],
    parser_hint: Optional[str],
    job_id: str,
    temp_path: Optional[str] = None,
):
    """Execute the 6-stage v2 ingestion pipeline in a background thread.

    Stages: DETECTING → PREPROCESSING → PARSING → NORMALIZATION → CHUNKING → INDEXING
    """
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        registry = CapabilityRegistry()

        # ── Stage 1: DETECTING ───────────────────────────────────────────
        manager.advance_stage(job_id, JobStage.DETECTING.value)
        parser_router = registry.get_instance("parser_router")
        detected_type = parser_router.detect_content_type(source_uri, hint=content_type)
        logger.debug(f"Job {job_id}: detected type = {detected_type}")

        # ── Stage 2: PREPROCESSING ───────────────────────────────────────
        manager.advance_stage(job_id, JobStage.PREPROCESSING.value)
        parse_source = temp_path or source_uri
        # Validate source exists for local paths
        if not temp_path and not os.path.exists(parse_source):
            raise FileNotFoundError(f"Source not found: {parse_source}")

        if cancel_check():
            raise CancellationError("Job cancelled during preprocessing")

        # ── Stage 3: PARSING ─────────────────────────────────────────────
        manager.advance_stage(job_id, JobStage.PARSING.value)
        result = parser_router.parse(parse_source, detected_type, cancel_check)

        if cancel_check():
            raise CancellationError("Job cancelled after parsing")

        # ── Stage 4: NORMALIZATION ───────────────────────────────────────
        manager.advance_stage(job_id, JobStage.NORMALIZATION.value)

        # Multi-page documents (PDF): process per-page for citation granularity
        if result.pages:
            _process_multipage(
                result, source_uri, user_metadata, job_id,
                manager, cancel_check, registry,
            )
        else:
            _process_singlepage(
                result, source_uri, user_metadata, job_id,
                manager, cancel_check, registry,
            )

        manager.complete_job(job_id)
        logger.info(f"Job {job_id} completed for '{source_uri}'")

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during v2 processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _process_singlepage(
    result, source_uri, user_metadata, job_id,
    manager, cancel_check, registry,
):
    """Handle single-content documents (text, HTML, Markdown)."""
    normalized_text = normalize_text(result.content_text)

    if not normalized_text.strip():
        logger.warning(f"Job {job_id}: empty content after normalization — skipping.")
        return

    # ── Stage 5: CHUNKING ────────────────────────────────────────────
    manager.advance_stage(job_id, JobStage.CHUNKING.value)
    doc = ParsedDocument(
        source_path=source_uri,
        canonical_doc_id=source_uri,
        page_title=result.page_title,
        content_text=normalized_text,
        language=result.language,
        images=result.images,
        user_metadata=user_metadata,
    )
    chunks = registry.get_instance("chunker").create_chunks(doc)

    if cancel_check():
        raise CancellationError("Job cancelled during chunking")

    # ── Stage 6: INDEXING ────────────────────────────────────────────
    manager.advance_stage(job_id, JobStage.INDEXING.value)
    client = get_client()
    upsert_chunks(client, chunks, cancel_check=cancel_check)


def _process_multipage(
    result, source_uri, user_metadata, job_id,
    manager, cancel_check, registry,
):
    """Handle multi-page documents (PDF) with per-page citation granularity."""
    chunker = registry.get_instance("chunker")
    all_chunks = []

    for page in result.pages:
        if cancel_check():
            raise CancellationError("Job cancelled during multipage normalization")

        page_text = normalize_text(page["text"])
        if not page_text.strip():
            continue

        doc_id = f"{source_uri}#p{page['page_number']}"
        parsed_doc = ParsedDocument(
            source_path=source_uri,
            canonical_doc_id=doc_id,
            page_title=result.page_title,
            content_text=page_text,
            images=[],
            user_metadata=user_metadata,
        )

        page_chunks = chunker.create_chunks(parsed_doc)
        for chunk in page_chunks:
            chunk.metadata.section_path = f"Page {page['page_number']}"

        all_chunks.extend(page_chunks)

    if not all_chunks:
        logger.warning(f"Job {job_id}: no chunks produced after normalization — skipping.")
        return

    # ── Stage 5: CHUNKING ────────────────────────────────────────────
    manager.advance_stage(job_id, JobStage.CHUNKING.value)

    if cancel_check():
        raise CancellationError("Job cancelled during chunking")

    # ── Stage 6: INDEXING ────────────────────────────────────────────
    manager.advance_stage(job_id, JobStage.INDEXING.value)
    client = get_client()
    upsert_chunks(client, all_chunks, cancel_check=cancel_check)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=IngestResponseV2,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_document_v2(
    payload: DocumentIngestRequestV2,
    background_tasks: BackgroundTasks,
) -> IngestResponseV2:
    """Generic multi-parser ingestion (JSON body with ``source_uri``)."""
    logger.debug(f"v2 ingest request: source_uri={payload.source_uri}")
    manager = JobManager()
    job = manager.create_job(source=payload.source_uri, job_type="v2_document")
    background_tasks.add_task(
        process_document_v2,
        payload.source_uri,
        payload.content_type,
        payload.user_metadata,
        payload.parser_hint,
        job.id,
    )
    return IngestResponseV2(
        status="accepted",
        message="Document accepted for processing",
        job_id=job.id,
    )


@router.post(
    "/upload",
    response_model=IngestResponseV2,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document_v2(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_path: str = Form(...),
    content_type: str = Form(None),
    user_metadata: str = Form(None),
) -> IngestResponseV2:
    """Generic multi-parser ingestion (multipart file upload)."""
    logger.debug(f"v2 upload request: filename={file.filename}")

    # Deserialise JSON-encoded user_metadata from form field
    parsed_metadata = None
    if user_metadata:
        try:
            parsed_metadata = _json.loads(user_metadata)
        except _json.JSONDecodeError:
            raise HTTPException(
                status_code=422,
                detail=[{"field": "user_metadata", "msg": "Invalid JSON in user_metadata form field"}],
            )
        try:
            validate_user_metadata(parsed_metadata)
        except UserMetadataValidationError as e:
            raise HTTPException(status_code=422, detail=e.details)

    manager = JobManager()
    job = manager.create_job(source=source_path, job_type="v2_upload")

    # Save the uploaded file to a temporary location
    suffix = os.path.splitext(file.filename or "")[1] or ""
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(temp_fd)

    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(
        process_document_v2,
        source_path,
        content_type,
        parsed_metadata,
        None,  # parser_hint
        job.id,
        temp_path=temp_path,
    )

    return IngestResponseV2(
        status="accepted",
        message=f"File '{file.filename}' accepted for processing",
        job_id=job.id,
    )
