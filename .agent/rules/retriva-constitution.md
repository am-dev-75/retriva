---
description: Constitution for PDF injector support
alwaysApply: true
---

# Retriva Constitution — PDF Injector

## Product law
- Retriva must support indexing local PDF documents as a first-class ingestion mode.
- PDF-derived chunks must remain compatible with existing retrieval, grounding, and citation behavior.
- OCR is not required for baseline PDF ingestion.

## Architecture law
- Introduce PDF support as a dedicated injector implementation.
- Reuse shared chunking, indexing, language metadata, and citation abstractions where possible.
- Preserve modularity so OCR or advanced PDF enrichment can be added later without redesign.

## Scope law
Out of scope for this increment:
- mandatory OCR
- table structure perfection beyond text extraction
- UI redesign
- replacing existing injectors
