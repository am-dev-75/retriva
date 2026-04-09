---
name: retriva-domain-context
description: Provides domain context and roadmap for the Retriva RAG chatbot PoC.
---

# Retriva Domain Context

Retriva is a RAG chatbot initiative for technical documentation about embedded systems and electronics boards.

## Current target
**PoC v0.1.1** is intentionally small:
- local static HTML mirror ingestion
- explicit `wget`-mirror assumptions
- section-aware chunking
- dense retrieval only
- Streamlit chat UI
- grounded answers with citations
- no user-facing agentic behavior
