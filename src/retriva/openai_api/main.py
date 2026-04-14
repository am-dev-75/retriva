# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from retriva.openai_api.routers import chat_completions, models
from retriva.indexing.qdrant_store import init_collection, get_client
from retriva.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Retriva OpenAI-compatible API...")
    try:
        client = get_client()
        init_collection(client)
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant during startup: {e}")

    # Load extensions (no-op if RETRIVA_EXTENSIONS is empty)
    from retriva.registry import CapabilityRegistry
    CapabilityRegistry().load_extensions()

    yield
    # Shutdown
    logger.info("Shutting down OpenAI-compatible API...")


from retriva.config import VERSION
app = FastAPI(
    title="Retriva OpenAI-Compatible API",
    version=VERSION,
    description=(
        "OpenAI-compatible chat completions and model listing for "
        "Open WebUI integration."
    ),
    lifespan=lifespan,
)

# Allow cross-origin requests — Open WebUI may run on a different host/port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_completions.router)
app.include_router(models.router)
