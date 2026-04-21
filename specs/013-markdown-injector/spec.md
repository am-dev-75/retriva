# Feature Spec — 013 Markdown Injector

## Goal
Add a new injector that can index local Markdown files from a recursively explored directory root, preserving structural landmarks like headings and section hierarchy for high-precision retrieval and citations.

## Background
Retriva supports several ingestion modes (HTML mirror, standalone images, plain text, MediaWiki exports, and PDF). A Markdown-specific ingestion mode is required to allow local `.md` and `.markdown` document sets (like documentation sites or personal notes) to be ingested with awareness of their structure.

## In scope
- Recursive directory discovery starting from a user-supplied root.
- Detection of local Markdown files (`.md`, `.markdown`).
- Extraction of Markdown text with structural awareness (headings, lists, code fences).
- Section-aware metadata generation (derived titles, heading paths).
- A new `markdown` injector implementation integrated into the CLI.
- New backend API endpoint `/api/v1/ingest/markdown`.
- Reuse of existing downstream chunk/index/citation pipelines.

## Out of scope
- HTML rendering as a requirement for ingestion.
- Replacing or modifying existing injectors.
- UI changes (handled by existing generic retrieval UI).
- Executable notebook semantics (.ipynb).

## Functional requirements

### FR1 — Recursive discovery
The system shall recursively explore the supplied root directory and detect candidate Markdown files. It must skip excluded directories (e.g., `.git`, `node_modules`).

### FR2 — New injector implementation
The system shall implement Markdown support as a dedicated injector (`markdown`) rather than folding it into the default generic ingestion pipeline.

### FR3 — Markdown structural parsing
The system shall parse Markdown content to identify:
- Document title (usually the first H1).
- Section hierarchy (nested headings).
- Content blocks (prose, code fences, lists).

### FR4 — Section-aware metadata
The system shall generate metadata for each document/section including:
- `doc_id`: Unique identifier for the file.
- `source_path`: Relative or canonical path to the file.
- `title`: Document title.
- `section_path`: Breadcrumb of headings (e.g., "Architecture > Components > Injectors").

### FR5 — CLI support
The CLI shall support `--injector markdown` for `ingest` and `reindex` commands.

### FR6 — Citation/debug metadata
The emitted documents/chunks shall preserve enough metadata for accurate citations in the RAG pipeline.

## Acceptance criteria
- [ ] User can run `retriva ingest --path /docs --injector markdown`.
- [ ] Subdirectories are traversed recursively.
- [ ] Markdown files are parsed and section hierarchy is extracted.
- [ ] Content is searchable via the Retriva API with correct citations.
- [ ] No regression in existing `html`, `pdf`, or `mediawiki` ingestion.
- [ ] The repository root `README.md` remains untouched.
