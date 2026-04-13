# Feature Spec — True Cross-Language Retrieval

## Goal
Implement seamless, true cross-language retrieval and question answering for English and Italian using the existing shared multilingual retrieval space provided by `baai/bge-m3`, mitigating the need for runtime LLM translation while ensuring the generated answer is provided in the user's querying language.

## In scope
- Extracting and storing language metadata (`language: str`) for documents/chunks during ingestion.
- Indexing English and Italian content into a shared multilingual space natively.
- Running similarity queries directly across languages within that single space.
- Strictly enforcing systemic prompts to format the LLM answer in the user's spoken language.
- Preserving source-language metadata entirely through to Streamlit citations to clarify context provenance.

## Out of scope
- Pre-translating document content in bulk at ingestion time.
- Applying runtime LLM translations of the query as a required default fallback loop (may be visited behind a flag strictly for experimentation).
- Broadening language alignment support beyond English and Italian.
