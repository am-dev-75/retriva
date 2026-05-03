# API

## Introduction

API is provided by multiple, independently deployable microservices:

* **Ingestion API (implemented in Retriva core)**: Dedicated to document processing. It handles content extraction, section-aware chunking, embedding generation, and indexing into the vector store. It manages both high-volume reindexing and real-time document updates.
* **OpenAI-compatible Chat API (implemented in Retriva core)**: Provides a standardized interface for the RAG pipeline. It implements the `/v1/chat/completions` and `/v1/models` endpoints, executing context retrieval, re-ranking, and prompt construction.
* **Open WebUI Adapter**: A thin control plane that bridges Open WebUI with Retriva. It performs intent classification to separate user queries from UI-level control prompts, maintains ephemeral ingestion context, and orchestrates document synchronization. This is the actual sofwtare interface seen by Open WebUI, although logic implementation is contained in the Retriva core codebase.


