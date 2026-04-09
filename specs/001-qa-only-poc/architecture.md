# Architecture — 001 Q&A-only PoC

## Style
A **modular monolith** written in Python.

## Suggested package structure
```text
src/retriva/
  config.py
  cli.py
  domain/models.py
  ingestion/mirror.py
  ingestion/discover.py
  ingestion/html_parser.py
  ingestion/normalize.py
  ingestion/chunker.py
  indexing/embeddings.py
  indexing/qdrant_store.py
  qa/retriever.py
  qa/prompting.py
  qa/answerer.py
  ui/streamlit_app.py
  utils/language.py
  utils/citations.py
```

## Pipelines
### Ingestion
1. discover candidate HTML files from the local `wget` mirror (`MIRROR_BASE_PATH`)
2. parse and isolate main content using explicit selectors (`#content`, `#mw-content-text`, `main`, `.mw-parser-output`), removing boilerplate (nav, footer, script, style)
3. normalize extracted text, resolving `wget`'s rewritten local links to absolute canonical URLs (`CANONICAL_BASE_URL`)
4. build section-aware chunks
5. compute embeddings
6. upsert into Qdrant

### Query
1. receive question
2. embed question
3. retrieve top-k chunks
4. assemble grounded prompt
5. call chat model
6. render answer + citations + debug payload
