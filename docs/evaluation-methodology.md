# Evaluation Methodology — Bilingual Regression and Retrieval Benchmarking

## Goal
Provide a small, deterministic evaluation suite that catches regressions in English/Italian retrieval behavior.

## Evaluation dimensions
1. **Retrieval correctness**
   - compare retrieved top-k documents against expected relevant documents
2. **Cross-language reachability**
   - verify EN queries can surface IT evidence and IT queries can surface EN evidence
3. **Answer behavior**
   - verify the answer language matches the query language
4. **Citation behavior**
   - verify grounded citations are present and point to relevant source documents
5. **Fallback behavior**
   - verify unsupported questions still trigger the expected insufficient-evidence response

## Suggested metrics
- `recall_at_k`
- `precision_at_k`
- `first_relevant_rank` (optional)
- `response_language_match`
- `citation_doc_match`

## Suggested verification flow
1. index the bilingual fixture corpus
2. run each benchmark query through retrieval only
3. compute retrieval metrics
4. run each benchmark query through the full QA path
5. record answer language and cited document ids
6. compare against expectations
