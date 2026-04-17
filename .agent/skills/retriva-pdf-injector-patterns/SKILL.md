---
name: retriva-pdf-injector-patterns
description: Guidance for building a local PDF injector for Retriva.
---

# Retriva PDF Injector Patterns

## Core input shape
The input is a recursive directory containing one or more `.pdf` files.

## Preferred processing flow
1. recursively scan the root directory
2. detect candidate PDF files
3. extract embedded text page by page
4. preserve page numbers and document-level metadata
5. emit document/chunk objects compatible with the existing indexing pipeline
6. keep enough metadata for citations and debugging

## Guardrails
- Do not require OCR for PDFs with extractable text
- Skip encrypted or unreadable PDFs gracefully with diagnostics
- Keep chunk metadata page-aware for citations
