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

from fastapi import APIRouter, HTTPException, status
from retriva.ingestion_api.schemas import JobResponse
from retriva.ingestion_api.job_manager import JobManager, TERMINAL_STATES, JobStatus
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
async def list_jobs():
    """List all tracked ingestion jobs."""
    manager = JobManager()
    jobs = manager.list_jobs()
    return [JobResponse(**j.to_dict()) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get the status of a specific job."""
    manager = JobManager()
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**job.to_dict())


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str):
    """
    Request cooperative cancellation of a job.

    - Running/pending → 202 Accepted (cancelling)
    - Already cancelling/cancelled → 200 OK (idempotent)
    - Completed/failed → 409 Conflict
    - Unknown → 404
    """
    manager = JobManager()
    job = manager.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status in (JobStatus.CANCELLING, JobStatus.CANCELLED):
        # Idempotent — already cancelling or cancelled
        return JobResponse(**job.to_dict())

    if job.status in TERMINAL_STATES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job in '{job.status.value}' state",
        )

    manager.request_cancel(job_id)
    # Re-fetch after state change
    job = manager.get_job(job_id)
    logger.info(f"Cancellation requested for job {job_id}")

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=JobResponse(**job.to_dict()).model_dump(),
    )