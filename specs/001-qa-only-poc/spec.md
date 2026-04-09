# Feature Spec — 001 Q&A-only PoC

## Goal
Build the first usable vertical slice of **Retriva**: a question-answering-only RAG chatbot that ingests a local static mirror and answers in English or Italian with grounded retrieval and citations.

## Input assumption
The primary tested input format is a **local static mirror created with `wget`**, compatible with:

```bash
wget --mirror --convert-links --page-requisites --no-parent https://wiki.dave.eu
```

The implementation targets the filesystem artifact, not live MediaWiki APIs.

## In scope
1. ingest a local static website mirror from the filesystem
2. discover HTML content pages (`.html`, `.htm`, `index.html`) and ignore obvious non-content assets (CSS, JS, fonts, unsupported media)
3. extract page title, section hierarchy, paragraphs, lists, tables-as-text, and nearby image textual context
4. create section-aware text chunks with explicit metadata (`doc_id`, `source_path`, `page_title`, `section_path`, `chunk_id`, `chunk_index`, `chunk_type`, `language`)
5. create embeddings through an OpenAI-compatible embeddings endpoint
6. store and query chunks in Qdrant using dense retrieval only
7. answer user questions through an OpenAI-compatible chat endpoint
8. provide a Streamlit chat UI with citations and debug view
9. support a clear fallback when evidence is insufficient
10. provide CLI commands for ingest / reindex / smoke test

## Out of scope
- OCR or VLM-based image understanding
- hybrid retrieval or reranking
- external APIs
- auth / RBAC
- live sync
- agentic features
