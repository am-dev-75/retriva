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
Ingestion endpoint for PDF pages.

Receives pre-extracted plain text from a single PDF page (the CLI
handles parsing and sends one request per page for page-level
citation granularity).
"""

from fastapi import APIRouter, BackgroundTasks, status, UploadFile, File, Form
import tempfile
import os
import shutil
from pathlib import Path
from retriva.ingestion_api.schemas import PdfIngestRequest, IngestResponse
from retriva.domain.models import ParsedDocument
from retriva.indexing.qdrant_store import get_client, upsert_chunks
from retriva.ingestion_api.job_manager import JobManager, CancellationError
from retriva.registry import CapabilityRegistry
from retriva.logger import get_logger

# Import module to trigger default registration
import retriva.ingestion.chunker  # noqa: F401 — registers DefaultChunker

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


def process_pdf_page_in_background(payload: PdfIngestRequest, job_id: str):
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        logger.debug(
            f"Processing PDF page in background: "
            f"'{payload.page_title}' p.{payload.page_number}"
        )

        if not payload.content_text.strip():
            logger.warning(
                f"Empty content for PDF page {payload.page_number} "
                f"of '{payload.page_title}' — skipping."
            )
            manager.complete_job(job_id)
            return

        doc_id = f"{payload.source_path}#p{payload.page_number}"
        doc = ParsedDocument(
            source_path=payload.source_path,
            canonical_doc_id=doc_id,
            page_title=payload.page_title,
            content_text=payload.content_text,
            images=[],
            user_metadata=payload.user_metadata,
        )

        # Override section_path in chunks for page-level citations
        registry = CapabilityRegistry()
        chunks = registry.get_instance("chunker").create_chunks(doc)
        for chunk in chunks:
            chunk.metadata.section_path = f"Page {payload.page_number}"

        client = get_client()
        upsert_chunks(client, chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)

        logger.info(
            f"PDF page {payload.page_number}/{payload.total_pages} "
            f"of '{payload.page_title}' indexed — {len(chunks)} chunk(s)"
        )

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during PDF processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")

def process_pdf_upload_in_background(temp_path: str, source_path: str, page_title: str, job_id: str, user_metadata=None):
    logger.debug(f"process_pdf_upload_in_background")
    logger.debug(f"user_metadata={user_metadata}")
    logger.debug(f"source_path={source_path}")
    logger.debug(f"job_id={job_id}")
    manager = JobManager()
    manager.start_job(job_id)
    cancel_check = lambda: manager.is_cancel_requested(job_id)

    try:
        from retriva.ingestion.pdf_parser import parse_pdf
        
        logger.debug(f"Parsing uploaded PDF file from temporary path: {temp_path}")
        doc = parse_pdf(Path(temp_path))
        if doc is None:
            logger.warning(f"Skipping unreadable PDF upload: {source_path}")
            manager.complete_job(job_id)
            return

        if not doc.pages:
            logger.warning(f"No extractable text in PDF upload {source_path} — skipping.")
            manager.complete_job(job_id)
            return

        registry = CapabilityRegistry()
        chunker = registry.get_instance("chunker")
        client = get_client()

        chunks = []
        for page in doc.pages:
            if cancel_check():
                break

            doc_id = f"{source_path}#p{page.page_number}"
            parsed_doc = ParsedDocument(
                source_path=source_path,
                canonical_doc_id=doc_id,
                page_title=page_title or doc.title,
                content_text=page.text,
                images=[],
                user_metadata=user_metadata,
            )

            page_chunks = chunker.create_chunks(parsed_doc)
            for chunk in page_chunks:
                chunk.metadata.section_path = f"Page {page.page_number}"
            
            chunks.extend(page_chunks)

        if cancel_check():
            raise CancellationError("Job cancelled before upserting chunks")
            
        upsert_chunks(client, chunks, cancel_check=cancel_check)
        manager.complete_job(job_id)

        logger.info(
            f"PDF file '{page_title or doc.title}' indexed — {len(doc.pages)} pages, {len(chunks)} chunk(s)"
        )

    except CancellationError:
        manager.mark_cancelled(job_id)
        logger.info(f"Job {job_id} cancelled during PDF upload processing")
    except Exception as e:
        manager.fail_job(job_id, str(e))
        logger.error(f"Job {job_id} failed: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post(
    "/pdf",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_pdf(
    payload: PdfIngestRequest,
    background_tasks: BackgroundTasks,
):
    """Ingest a single PDF page (pre-extracted plain text)."""
    logger.debug(
        f"Received PDF page: '{payload.page_title}' "
        f"p.{payload.page_number}/{payload.total_pages}"
    )
    manager = JobManager()
    job = manager.create_job(source=payload.source_path, job_type="pdf")
    background_tasks.add_task(process_pdf_page_in_background, payload, job.id)
    return IngestResponse(
        status="accepted",
        message=(
            f"PDF page {payload.page_number} of "
            f"'{payload.page_title}' accepted for processing"
        ),
        job_id=job.id,
    )


@router.post(
    "/upload/pdf",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_pdf_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_path: str = Form(...),
    page_title: str = Form(None),
    user_metadata: str = Form(None),
):
    """Ingest a raw PDF file upload."""
    logger.debug(f"Received PDF file upload: '{file.filename}'")
    logger.debug(f"user_metadata={user_metadata}")
    logger.debug(f"source_path={source_path}")
    logger.debug(f"page_title={page_title}")
    logger.debug(f"file={file}")

    # Deserialise JSON-encoded user_metadata from form field
    parsed_metadata = None
    if user_metadata:
        import json as _json
        try:
            parsed_metadata = _json.loads(user_metadata)
        except _json.JSONDecodeError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail=[{"field": "user_metadata", "msg": "Invalid JSON in user_metadata form field"}],
            )
        from retriva.ingestion_api.schemas import validate_user_metadata, UserMetadataValidationError
        try:
            validate_user_metadata(parsed_metadata)
        except UserMetadataValidationError as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=e.details)

    manager = JobManager()
    job = manager.create_job(source=source_path, job_type="pdf_upload")
    
    # Save the file to a temporary location
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(temp_fd)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    background_tasks.add_task(
        process_pdf_upload_in_background, 
        temp_path, 
        source_path, 
        page_title or file.filename, 
        job.id,
        user_metadata=parsed_metadata,
    )
    
    return IngestResponse(
        status="accepted",
        message=f"PDF file '{file.filename}' accepted for processing",
        job_id=job.id,
    )