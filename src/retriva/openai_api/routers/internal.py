# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter, HTTPException, status
from retriva.config import settings
from retriva.profiler import get_recent_logs

router = APIRouter(prefix="/internal/profiler", tags=["internal"])

@router.get("/log")
async def get_profiler_logs():
    """
    Expose recent structured profiler logs.
    Available only when ENABLE_INTERNAL_PROFILER=true.
    """
    if not settings.enable_internal_profiler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profiler is disabled."
        )
    
    return get_recent_logs()
