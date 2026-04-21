---
description: Constitution for Markdown injector support
alwaysApply: true
---

# Retriva Constitution — Markdown Injector

## Product law
- Retriva must support indexing local Markdown documents as a first-class ingestion mode.
- Markdown-derived chunks must remain compatible with existing retrieval, grounding, and citation behavior.
- Markdown structure should improve chunk boundaries, not be discarded blindly.

## Architecture law
- Introduce Markdown support as a dedicated injector implementation.
- Reuse shared chunking, indexing, language metadata, and citation abstractions where possible.
- Preserve modularity so advanced Markdown-aware enrichment can be added later without redesign.

## Scope law
Out of scope for this increment:
- full static-site rendering
- executing embedded code blocks
- image OCR/VLM as a requirement
- UI redesign
- replacing existing injectors
