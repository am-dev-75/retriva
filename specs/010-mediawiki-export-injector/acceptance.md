# Acceptance Criteria — 010 MediaWiki Native Export Injector

## Core functionality
- A user can run `python -m retriva.cli ingest --path /data/wiki-export
  --injector mediawiki_export` and have XML pages indexed.
- `*.xml` files are validated by sniffing for `<mediawiki` before parsing.
- Pages from namespace 0 (Main) are parsed; other namespaces (Talk,
  User, etc.) are skipped by default.
- Raw wikitext is converted to clean plain text before chunking.
- `[[File:…]]` / `[[Image:…]]` references are extracted and resolved
  against the local `assets/` subtree when present.
- Resolved images are VLM-enriched (via the registry) and stored as
  `chunk_type="image"` chunks.

## Metadata
- Every emitted chunk carries `doc_id`, `page_title`, `source_path`
  (XML file), `language`, and `chunk_type`.
- Citation metadata is sufficient for the QA pipeline to produce
  `[Page Title]` citations in Open WebUI.

## Backward compatibility
- Running `ingest` without `--injector` uses the existing HTML/image/text
  pipeline — zero behavior change.
- Existing `wget`-mirror ingestion, OpenAI API, and bilingual benchmark
  tests all pass unchanged.
- The repository root `README.md` is not modified.

## Isolation
- The HTML injector code (`html_parser.py`, `ingest_HTML.py`) is not
  modified.
- No new external Python dependencies are required (stdlib `xml` + `re`).

## Test coverage
- Unit tests for XML parsing (valid export, malformed XML, empty pages).
- Unit tests for wikitext-to-plaintext conversion edge cases.
- Unit tests for asset index building and case-insensitive resolution.
- Integration fixture test: XML + assets → API call → chunks created.
