# Technical Architecture — True Cross-Language Retrieval

## Native Multilingual Shared Space Focus
Instead of intercepting and mutating queries and chunks at runtime via LLM-based translation abstractions, this design directly embraces the intrinsic cross-lingual representation space of the baseline model, `baai/bge-m3`. This guarantees low latency routing while achieving high fidelity representation. 

## 1. Language Metadata Identification
To support context preservation, Retriva will assign a `language` property across the ingestion stack:
1. **HTML Parser**: In `ingestion/html_parser.py`, parsing targets the `lang` attribute from the initial HTML document tag if present. Fallback text heuristics can be used if `lang` is absent.
2. **Text / VLM Nodes**: Extend `ingest_image` and `ingest_text` router endpoints to optionally accept a language parameter, falling back to an `eng` default.
3. **Data Schema**: Pydantic ingestion data models (`schemas.py`) carry forward a `language` string (en, it, etc.).

## 2. Shared Vector Space Indexing
When vector points are constructed in `qdrant_store.py`, `language` is stored firmly within Qdrant's payload:
```python
payload = {
    "source_path": chunk.source_path,
    "page_title": chunk.page_title,
    "chunk_index": chunk.chunk_index,
    "text": chunk.text,
    "language": chunk.language  # <-- NEW
}
```
Queries strictly use identical standard procedures: generating a single embedding array representing the user instruction to find dense matches in the multilingual Qdrant collection. Language metadata is passively surfaced with retrieved chunks.

## 3. Dynamic Answering Prompt 
Modifications are made to `qa/prompting.py` so the system prompt contains an invariant instruction for the model to behave natively bilingual:
> "Identify the language of the user's question. Formulate your complete answer strictly in the exact language used by the user, even if the provided chunks are documented entirely in a different language."

## 4. Front-End Citation Parity 
The pipeline surfaces the chunk `language` via `qa/answerer.py` and `openai_api/routers/chat_completions.py`. The Streamlit visual design displays source chunk languages clearly attached to citations, empowering the end-user to know the language provenance of the fact utilized to render their answer.
