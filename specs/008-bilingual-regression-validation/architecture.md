# Architecture — Bilingual Regression Validation

## Design principle
Validation must be externalized from the product logic and use a controlled bilingual corpus.

## Recommended structure
- `eval/fixtures/bilingual_corpus/` for source documents
- `specs/008-bilingual-regression-validation/benchmark-cases.yaml` for expected outcomes
- product tests / scripts consume the benchmark definitions and compute metrics

## Validation layers
1. **Retrieval-only validation**
   - measures recall/precision against expected relevant docs
2. **Full QA validation**
   - checks answer language and citation integrity
3. **Regression gating**
   - compares current results against expected thresholds / exact cases
