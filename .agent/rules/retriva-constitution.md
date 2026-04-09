---
description: Always-on constitution for the Retriva v0.1.1 Q&A-only PoC
alwaysApply: true
---

# Retriva Constitution

## Product law
- The current target is **Retriva PoC v0.1.1: Q&A-only**.
- Answer only from the indexed knowledge base.
- Every answer must include citations.
- If evidence is insufficient, use an explicit fallback.
- Support English and Italian.

## Architecture law
- Use Python.
- Use Streamlit for the first UI.
- Use OpenAI-compatible APIs for chat and embeddings.
- Keep a modular monolith for v0.1.1.

## Data law
- The first source is a local static MediaWiki mirror.
- The primary tested artifact is created with:
  `wget --mirror --convert-links --page-requisites --no-parent <url>`
- Ingest text HTML content and nearby image textual context only.
- Do not implement OCR or VLM analysis yet.

## Scope law
Out of scope for v0.1.1:
- hybrid retrieval
- reranking
- OCR / VLM image enrichment
- external APIs
- RBAC / auth
- live sync
- agentic features
