# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import APIRouter
from retriva.openai_api.schemas import ModelInfo, ListModelsResponse

router = APIRouter(tags=["models"])

# Fixed model entry — Retriva exposes itself as a single unified model.
_RETRIVA_MODEL = ModelInfo(id="retriva", owned_by="retriva")


@router.get("/v1/models", response_model=ListModelsResponse)
async def list_models():
    """
    Returns the list of available models.

    Open WebUI calls this on connection to discover which models are
    available.  Retriva always returns a single model: ``retriva``.
    """
    return ListModelsResponse(data=[_RETRIVA_MODEL])
