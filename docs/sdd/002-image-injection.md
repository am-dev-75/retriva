# SDD Pack — v0.2 Image Injection

This document describes the **v0.2 image injection increment** for Retriva.

## Purpose

Extend the existing HTML ingestion pipeline so that images referenced by HTML pages
are discovered, normalized, chunked, and indexed using the same conceptual flow.

## Key constraints

- Images are always anchored to HTML pages
- No OCR or VLM is performed
- Retrieval logic is unchanged
- The repository root README.md must remain untouched

## Expected outcome

After v0.2:
- HTML-only ingestion still works
- Images are injectable assets
- Image-derived chunks exist in the index
