# SDD Pack — Hybrid Retrieval Selection for Retriva OSS

## Status
Proposed

## Scope
Retriva OSS Core

## Summary
This SDD introduces **hybrid retrieval selection** in Retriva OSS, combining vector-similarity ranking with re-ranked results to preserve evidentiary recall while improving precision. Hybrid selection ensures that implicit, non-linguistic evidence (e.g., measurements, tables, plots) is retained even when aggressive re-ranking is enabled.

The hybrid strategy is enabled by default and designed to be cleanly overridable by Retriva Pro.

---

## Motivation

Re-ranking improves precision but can suppress implicit or inferential evidence that is weakly represented in embeddings (e.g., numeric measurements, plots, PDF tables). This has been observed to cause answer regressions for engineering-style questions such as maximum or observed values.

Hybrid selection restores recall by guaranteeing that a small subset of high-similarity vector results is always preserved alongside re-ranked results.

---

## Architectural Principles

- Vector search maximizes recall
- Re-ranking maximizes precision
- Hybrid selection balances both
- Deterministic and bounded behavior
- OSS-safe defaults
- Explicit override seam for Retriva Pro

---

## Updated Retrieval Pipeline

```
Query
  ↓
Vector Search (ANN)
  ↓
Initial Vector Ranking
  ↓
Re-Ranking (optional)
  ↓
Hybrid Selection (NEW)
  ↓
Prompt Construction
  ↓
Inference
```

---

## Functional Requirements

### FR-1 — Hybrid Selection Enablement

Hybrid selection MUST be enabled by default.

```env
ENABLE_HYBRID_RETRIEVAL_SELECTION=true
```

When disabled, the system MUST fall back to pure re-ranking behavior.

---

### FR-2 — Hybrid Composition

The final context MUST be composed of:

- Top **M** chunks by re-ranking score
- Top **L** chunks by original vector similarity (deduplicated)

Conceptual definition:

```
final_context = top_M_by_rerank ∪ top_L_by_vector
```

---

### FR-3 — Configuration via .env

Hybrid selection parameters MUST be configurable via environment variables:

```env
HYBRID_RERANK_KEEP_TOP_M=4
HYBRID_VECTOR_KEEP_TOP_L=2
```

Constraints:
- M + L MUST be ≤ RETRIEVAL_RERANK_TOP_N
- Deduplication MUST be applied before prompt construction

---

### FR-4 — Interaction with Re-Ranking

- Hybrid selection MUST be applied **after** re-ranking
- Re-ranking MUST operate only on RETRIEVAL_RERANK_CANDIDATES
- Vector-keep chunks MUST come from the original vector-ranked list

---

### FR-5 — OSS Implementation and Pro Override

Hybrid selection logic MUST be implemented behind a stable internal interface so that Retriva Pro may:

- Replace hybrid logic entirely
- Introduce adaptive or question-aware strategies
- Add document-family or metadata-based guarantees

No changes to adapter or OWUI are permitted.

---

## Profiling Requirements

### PR-1 — Existing Profiler Phases

Hybrid selection MUST reuse existing retrieval profiler phases:

- retrieval_vector_search_complete
- retrieval_reranking_complete

Hybrid selection itself MUST NOT add a new timing phase but MUST be included in retrieval_reranking_complete.

---

## Configuration Summary

| Variable | Default | Description |
|--------|--------|-------------|
| ENABLE_HYBRID_RETRIEVAL_SELECTION | true | Enable hybrid selection |
| HYBRID_RERANK_KEEP_TOP_M | 4 | Re-ranked chunks to keep |
| HYBRID_VECTOR_KEEP_TOP_L | 2 | Vector-ranked chunks to keep |

---

## Non-Goals

This SDD explicitly does NOT include:

- User-configurable hybrid logic
- OWUI UI changes
- Adapter logic changes
- LLM-based re-ranking in OSS
- Automatic question-type detection

---

## Acceptance Criteria

- Hybrid selection preserves implicit measurement evidence
- Re-ranking precision improvements are retained
- Answer regressions caused by over-aggressive re-ranking are eliminated
- Configuration is respected via .env
- Behavior is deterministic and bounded
- Retriva Pro can override logic cleanly

---

## Rationale

Hybrid selection resolves the inherent tension between recall and precision in RAG systems by preventing re-ranking from becoming a hard gatekeeper. This restores inferential capability while preserving the quality gains of re-ranking.

---

## One-Sentence Summary

Retriva OSS gains a hybrid retrieval selection stage that guarantees evidentiary recall by combining vector similarity and re-ranked results, preventing answer regressions caused by over-aggressive re-ranking.