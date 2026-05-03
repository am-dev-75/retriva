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
v2 job status endpoints.

Returns extended job status with pipeline stage information
(``current_stage``, ``stages_completed``).
"""

from fastapi import APIRouter, HTTPException, status

from retriva.ingestion_api.job_manager import JobManager
from retriva.ingestion_api.schemas_v2 import JobResponseV2
from retriva.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v2/jobs", tags=["v2-jobs"])


@router.get("", response_model=list[JobResponseV2])
async def list_jobs_v2():
    """List all v2 ingestion jobs with stage information."""
    manager = JobManager()
    jobs = manager.list_jobs()
    # Filter to v2 jobs only
    v2_jobs = [j for j in jobs if j.job_type.startswith("v2_")]
    return [JobResponseV2(**j.to_dict()) for j in v2_jobs]


@router.get("/{job_id}", response_model=JobResponseV2)
async def get_job_v2(job_id: str):
    """Get the status of a specific job with pipeline stage information."""
    manager = JobManager()
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return JobResponseV2(**job.to_dict())
