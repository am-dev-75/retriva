# Implementation Plan — 001 Q&A-only PoC

## Phase 1
- bootstrap Python project
- add config and domain models

## Phase 2
- implement `wget`-mirror discovery
- implement HTML content extraction and normalization
- implement `wget` canonical URL reconstruction and relative link unrolling
- implement section-aware chunking
- add parser/chunker tests

## Phase 3
- implement OpenAI-compatible embeddings adapter
- implement Qdrant adapter
- implement ingest / reindex CLI

## Phase 4
- implement grounded QA core with fallback
- add tests for fallback and citations

## Phase 5
- build Streamlit UI with citations and debug panel

## Phase 6
- verify against acceptance criteria
