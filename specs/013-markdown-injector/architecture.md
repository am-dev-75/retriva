# Architecture — Markdown Injector

## Design principle
The Markdown injector follows the "sidecar" pattern for specialized formats, adding a parallel ingestion path while reusing the core indexing pipeline.

## Components

### 1. CLI Integration (`src/retriva/cli.py`)
- Adds `run_markdown_ingest` function.
- Extends `--injector` choices with `markdown`.
- Handles recursive discovery of `.md` and `.markdown` files.

### 2. Markdown Parser (`src/retriva/ingestion/markdown_parser.py`) [NEW]
- Responsible for parsing raw Markdown into a `ParsedDocument` model.
- Identifies document title from the first `#` heading or filename.
- Implements section-splitting logic based on heading levels.
- Preserves structure for metadata: `{"title": "...", "sections": [{"heading": "...", "text": "..."}]}`.

### 3. Ingestion API (`src/retriva/ingestion_api/`)
- New endpoint `POST /api/v1/ingest/markdown`.
- Expects structured payload:
  ```json
  {
    "source_path": "docs/readme.md",
    "page_title": "Project README",
    "sections": [
      {"heading": "Introduction", "content": "..."},
      {"heading": "Installation", "content": "..."}
    ]
  }
  ```

## Processing flow
1. **Discovery**: CLI walks the target directory recursively, collecting Markdown files.
2. **Parsing**: Each file is parsed locally by `markdown_parser.py` to extract text and sections.
3. **Transmission**: Structured data is POSTed to the backend API.
4. **Indexing**: Backend splits sections into chunks, generates embeddings, and stores them in the vector database.

## Dependencies
- Use a lightweight Markdown parsing library (e.g., `marko` or `mistune`) to avoid complex regex maintenance, if feasible. Otherwise, implement a robust heading-based splitter.
