---
name: retriva-markdown-injector-patterns
description: Guidance for building a local Markdown injector for Retriva.
---

# Retriva Markdown Injector Patterns

## Core input shape
The input is a recursive directory containing one or more Markdown files, typically `.md` or `.markdown`.

## Preferred processing flow
1. recursively scan the root directory
2. detect candidate Markdown files
3. parse raw Markdown text while preserving structural landmarks
4. derive document title and section hierarchy from headings where practical
5. emit document/chunk objects compatible with the existing indexing pipeline
6. keep enough metadata for citations and debugging

## Guardrails
- Do not require rendering Markdown to HTML just to ingest it
- Preserve heading hierarchy and section anchors when useful
- Keep code fences distinguishable from prose in metadata or chunking decisions
