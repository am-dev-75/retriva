---
description: Constitution for MediaWiki native export injector
alwaysApply: true
---

# Retriva Constitution — MediaWiki Native Export Injector

## Product law
- Retriva must support ingestion from both static HTML mirrors and native MediaWiki export mirrors.
- The native export input is a filesystem tree containing XML export files and exported assets.
- The resulting indexed knowledge must remain grounded, cited, and compatible with existing QA flows.

## Architecture law
- Introduce the export-mirror support as a **new injector implementation**.
- Reuse shared chunking/indexing/citation abstractions where possible.
- Preserve the current modular architecture and extension seams.

## Scope law
Out of scope for this increment:
- live MediaWiki API crawling
- modifying the main retrieval architecture
- OCR/VLM enrichment unless already independently supported
- UI redesign
