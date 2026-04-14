# Implementation Plan — Bilingual Regression Validation

## Phase 1 — Fixture corpus
- add a tiny bilingual corpus with stable document ids
- ensure at least one concept exists only in EN and one only in IT
- ensure at least one concept exists in both languages

## Phase 2 — Benchmark cases
- define retrieval-only and full-QA cases
- record expected relevant docs
- record expected answer language and citation constraints

## Phase 3 — Validation implementation
- add scripts/tests to run retrieval-only evaluation
- add scripts/tests to run full-QA evaluation
- compute recall@k and precision@k

## Phase 4 — Regression usage
- document how to run the benchmark locally
- make results easy to compare across future releases
