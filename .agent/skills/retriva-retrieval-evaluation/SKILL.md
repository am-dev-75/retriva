---
name: retriva-retrieval-evaluation
description: Patterns for creating regression fixtures and retrieval metrics such as recall@k and precision@k.
---

# Retriva Retrieval Evaluation

## Recommended metrics
- Recall@k
- Precision@k
- MRR / first relevant rank (optional)
- Answer-language correctness
- Citation completeness

## Fixture design rules
- Keep documents short and semantically distinct
- Ensure at least one case where the best evidence exists only in the other language
- Record expected relevant document ids per query
- Avoid fragile exact-answer assertions when behavior can be semantically equivalent
