# SDD Pack — Retrieval Re-Ranking for Retriva OSS

## Status
Proposed

## Scope
Retriva OSS Core

## Summary
This SDD introduces a lightweight, bounded re-ranking stage in the Retriva OSS retrieval pipeline. The re-ranker improves retrieval quality by re-ordering the most relevant candidates returned by vector search before prompt construction. The re-ranking model and its settings are configurable via environment variables and the implementation is explicitly designed to be overridden by Retriva Pro.

## Motivation
Vector similarity alone often produces suboptimal ordering. A secondary re-ranking stage significantly improves grounding and answer quality while keeping latency bounded. This design ensures Retriva OSS gains quality improvements without sacrificing predictability or extensibility.

## Architectural Principles
- Two-stage retrieval (recall then precision)
- Enabled by default, configurable via .env
- Low-latency, deterministic OSS baseline
- Clean override path for Retriva Pro
- Fully observable via profiler integration

## Updated Retrieval Pipeline
Query → Vector Search → Initial Ranking → Re-Ranking → Top-N Selection → Prompt Construction → Inference

## Functional Requirements

### FR-1 — Enablement
Re-ranking MUST be enabled by default and configurable via environment variable:

ENABLE_RETRIEVAL_RERANKING=true

When disabled, vector search results MUST be used directly.

### FR-2 — Candidate Set Size
The number of candidates passed to the re-ranker MUST be configurable:

RETRIEVAL_RERANK_CANDIDATES=20

### FR-3 — Top-N Selection
The number of final contexts selected after re-ranking MUST be configurable:

RETRIEVAL_RERANK_TOP_N=8

This value MUST be less than or equal to RETRIEVAL_RERANK_CANDIDATES.

### FR-4 — Re-Ranking Model Configuration
The re-ranking model and its settings MUST be configurable via .env:

RETRIEVAL_RERANK_MODEL=bge-reranker-small
RETRIEVAL_RERANK_BATCH_SIZE=8
RETRIEVAL_RERANK_MAX_LENGTH=512

Retriva OSS MUST provide a default model and safe defaults for all settings.

### FR-5 — OSS Implementation and Pro Override
The OSS re-ranker MUST be implemented behind a stable internal interface so that Retriva Pro can replace it with a more advanced implementation without modifying the retrieval pipeline or adapter behavior.

## Profiling Requirements

### PR-1 — New Profiler Phases
Two profiler phases MUST be recorded:
- retrieval_vector_search_complete
- retrieval_reranking_complete

### PR-2 — Profiling Semantics
Re-ranking timing MUST include only scoring and sorting logic and use monotonic clocks.

## Configuration Summary
| Variable | Default | Description |
| ENABLE_RETRIEVAL_RERANKING | true | Enable or disable re-ranking |
| RETRIEVAL_RERANK_CANDIDATES | 20 | Number of candidates to re-rank |
| RETRIEVAL_RERANK_TOP_N | 8 | Number of final contexts |
| RETRIEVAL_RERANK_MODEL | bge-reranker-small | OSS re-ranking model |
| RETRIEVAL_RERANK_BATCH_SIZE | 8 | Batch size for re-ranking |
| RETRIEVAL_RERANK_MAX_LENGTH | 512 | Max input length |

## Non-Goals
- No LLM-based re-ranking in OSS
- No OWUI changes
- No adapter changes
- No dynamic user-level controls

## Acceptance Criteria
- Re-ranking improves ordering quality
- Re-ranking latency remains bounded
- Re-ranking can be disabled via .env
- Profiler records both retrieval phases
- Retriva Pro can override OSS implementation cleanly

## One-Sentence Summary
Retriva OSS gains a configurable, profiler-visible re-ranking stage with environment-controlled model selection and a clean override path for Retriva Pro.