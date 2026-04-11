---
description: Constitution for Retriva v0.2 image injection
alwaysApply: true
---

# Retriva Constitution — v0.2

## Product law

- The target is **v0.2: HTML + image injection**
- Images are injectable assets, not yet semantic knowledge
- No OCR or VLM is required in this version

## Architecture law

- Extend existing ingestion logic; do not replace it
- Image injection must mirror HTML injection structure
- Use the same chunk/indexing abstractions where possible

## Scope law

Out of scope:
- Image understanding
- Retrieval changes
- API exposure
- Async jobs
