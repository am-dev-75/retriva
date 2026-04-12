---
description: Constitution for Retriva Open WebUI integration (refined)
alwaysApply: true
---

# Retriva Constitution — Open WebUI Integration

## Product law
- Retriva acts as a **RAG backend**, not a UI
- Open WebUI is an external client
- Answers must be grounded and cite sources

## Architecture law
- Use REST APIs only
- Follow OpenAI-style request/response schemas
- Keep ingestion, retrieval, and chat logic decoupled

## Scope law
Out of scope:
- UI implementation
- Authentication / RBAC
- Hybrid retrieval or reranking
