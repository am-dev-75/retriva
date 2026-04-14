# Feature Spec — 008 Bilingual Regression Validation

## Goal

Provide a lightweight companion validation tool and benchmarking suite for English/Italian bilingual behavior. This validation suite guarantees that true cross-language retrieval (Milestone 007) and QA output fidelity do not regress over time.

## Background

Retriva natively supports ingesting English and Italian corpora into a shared dense multilingual vector space (`baai/bge-m3`). The language model (`qwen3.5-27b` via OpenRouter) is prompted to explicitly respond in the user's inferred query language, regardless of the retrieved text's language.

Without a dedicated regression test suite, any future prompt engineering, model migrations, or retrieval chunking optimizations run the risk of breaking:
- Cross-lingual retrieval capabilities
- The strict generation language-matching requirement

## In scope

### Verification Pipelines
- **Retrieval validation**: Ensures cross-lingual (EN $\rightarrow$ IT, IT $\rightarrow$ EN) requests reliably retrieve from the correct vector chunks.
- **Generative validation**: Ensures the generated text is in the expected language matching the query language.
- **Metadata validation**: Validates that retrieved source citations are perfectly populated with the original originating document languages.

### Test Architecture
- Fully deterministic HTML fixture sets injected dynamically during verification.
- Isolated test queries executing specific predefined `Expected Source` checks via a custom fixture definition (`benchmark-cases.yaml`).
- Evaluation scripts capable of calculating `Recall@k`, `Precision@k`, and `response_language_match`.

### Execution
To run the bilingual verification benchmark locally, execute the dedicated pytest test harness while asserting the virtual environment is sourced:

```bash
PYTHONPATH=src pytest tests/test_bilingual.py -s
```

## Out of scope

- Direct modifications to the Retriva product pipeline or system prompt logic.
- Testing any additional European languages beyond English and Italian.
- Complex latency/throughput benchmarking (the focus is exclusively on logical correctness).
- Force-translating embedded arrays externally.

## Constraints

- This validation suite must not negatively modify the repository root `README.md`.
- Evaluation fixtures must be small, deterministic, and highly human-reviewable.
- The product architecture and behavioral pipelines cannot be mutated during testing; this pack merely asserts against their active implementations.
