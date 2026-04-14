# Agent Instructions — Retriva Bilingual Regression Validation

## Mission
Add a **companion validation and benchmarking pack** for English/Italian bilingual behavior after true cross-language retrieval is implemented.

## Order of authority
1. `specs/008-bilingual-regression-validation/spec.md`
2. `specs/008-bilingual-regression-validation/acceptance.md`
3. `specs/008-bilingual-regression-validation/benchmark-cases.yaml`
4. `.agent/rules/retriva-constitution.md`
5. `docs/evaluation-methodology.md`

## Non-negotiable rules
- Do not modify the repository root `README.md`
- Do not change product behavior as part of this pack; this pack validates and measures it
- Cover all four bilingual pathways: EN→EN, IT→IT, EN→IT, IT→EN
- Keep fixtures small, deterministic, and human-reviewable
- Validate both **retrieval correctness** and **answering/citation behavior**
