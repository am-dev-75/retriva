# Acceptance Criteria — 008 Bilingual Regression Validation

## Validation Runner Requirements

A verification system must be written that executes the definitions outlined in the `benchmark-cases.yaml` array. The validation pipeline must safely test both components (retrieval capability and generative language matching) securely.

### Phase 1: Storage and Initialization
- **Deterministic Fixtures**: The runner must securely push the deterministic fixtures onto a pristine Qdrant collection or namespace to guarantee no overlaps with broad/real-world indexes.
- **Payload Extraction**: Every ingested fixture document must correctly surface the `language` trait attached transparently into `ChunkMetadata` before attempting queries natively.

### Phase 2: Retrieval Validation Constraints
For all cases in `benchmark-cases.yaml` under `expected_retrieval_ids`:
- `Recall@1` must be exactly equal to **1.0**. Because the factual cases are completely unambiguous and mutually exclusive, the correct cross-language document should explicitly index as the highest scored nearest neighbor chunk inside the embedding space.

### Phase 3: QA Generation & Citations Validation Constraints
- By issuing the `query_text` up into the REST router, the validation runner **must explicitly** evaluate the response string and correctly identify whether the language of the output explicitly mirrors `expected_answer_language`.
- If fallback behaviors triggers (like a `fr` query), the system must cleanly trigger the predefined error messaging behavior without inventing hallucinations.
- Validation must assert that returned OpenWebUI `citations` securely populate the HTTP schema payload mapped cleanly from the chunk indices inside the Vector store.

When the verification pipeline natively reports 100% on the core deterministic tests spanning the 4 permutations natively (EN->EN, IT->IT, EN->IT, IT->EN) transparently, the specifications for this Milestone regression testing parameter are actively satisfied.
