# Copyright (C) 2026 Andrea Marson (am.dev.75@gmail.com)

from fastapi import FastAPI
from contextlib import asynccontextmanager
from retriva.ingestion_api.routers import ingest, ingest_HTML, ingest_image, ingest_text, jobs
from retriva.indexing.qdrant_store import init_collection, get_client
from retriva.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Modular Injection API...")
    try:
        client = get_client()
        init_collection(client)
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant during startup: {e}")
    yield
    # Shutdown
    logger.info("Shutting down API...")

app = FastAPI(
    title="Retriva Modular Injection API",
    version="0.3.0",
    description="REST API for injecting documents into the Retriva RAG pipeline.",
    lifespan=lifespan
)

app.include_router(ingest.router)
app.include_router(ingest_HTML.router)
app.include_router(ingest_image.router)
app.include_router(ingest_text.router)
app.include_router(jobs.router)
