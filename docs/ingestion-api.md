# Retriva Ingestion API Reference

The Retriva Ingestion API provides endpoints for submitting documents, images, and raw chunks into the Retriva RAG pipeline.

All ingestion endpoints (except `/collection`) are asynchronous and return a `job_id` that can be used to track the status of the ingestion process.

## Base URL
Default: `http://127.0.0.1:8000/api/v1/ingest`

## Endpoints

### 1. Ingest HTML
`POST /html`

Ingests raw HTML content. The system will extract the title and main text content automatically.

**Payload:**
```json
{
  "source_path": "https://example.com/page",
  "page_title": "Example Page",
  "html_content": "<html>...</html>",
  "origin_file_path": "/path/to/local/file.html"
}
```

### 2. Ingest Markdown
`POST /markdown`

Ingests structured Markdown content, split into sections. This ensures high-precision retrieval with section-aware metadata.

**Payload:**
```json
{
  "source_path": "/path/to/local/file.md",
  "page_title": "Document Title",
  "sections": [
    {
      "heading": "Introduction",
      "content": "This is the intro..."
    },
    {
      "heading": "Installation",
      "content": "Steps to install..."
    }
  ]
}
```

### 3. Ingest PDF Page
`POST /pdf`

Ingests text from a single PDF page. This is typically called page-by-page by the CLI.

**Payload:**
```json
{
  "source_path": "/path/to/local/file.pdf",
  "page_title": "Document Title",
  "content_text": "Text from page 1...",
  "page_number": 1,
  "total_pages": 10
}
```

### 4. Ingest MediaWiki Page
`POST /mediawiki`

Ingests a page extracted from a MediaWiki XML export.

**Payload:**
```json
{
  "source_path": "/path/to/export.xml",
  "page_title": "Wiki Page",
  "content_text": "Plain text content...",
  "page_id": 123,
  "namespace": 0,
  "linked_assets": ["/path/to/image.png"]
}
```

### 5. Ingest Standalone Image
`POST /image`

Ingests an image for VLM-based enrichment (visual description).

**Payload:**
```json
{
  "source_path": "/path/to/image.png",
  "page_title": "image",
  "file_path": "/path/to/image.png"
}
```

### 6. Ingest Plain Text
`POST /text`

Ingests raw plain text.

**Payload:**
```json
{
  "source_path": "/path/to/note.txt",
  "page_title": "My Note",
  "content_text": "Hello world..."
}
```

### 7. Ingest Raw Chunks
`POST /chunks`

Ingests pre-processed `Chunk` objects directly.

**Payload:**
```json
{
  "chunks": [
    {
      "text": "Chunk content",
      "metadata": {
        "doc_id": "...",
        "source_path": "...",
        "page_title": "...",
        "section_path": "...",
        "chunk_id": "...",
        "chunk_index": 0
      }
    }
  ]
}
```

### 8. Clear Collection
`DELETE /collection`

Clears the vector database collection and re-initializes it. **Warning: This is a destructive operation.**

## Job Management

### Get Job Status
`GET /api/v1/jobs/{job_id}`

Returns the status of a specific ingestion job.

**Possible Statuses:**
- `queued`: Job is waiting for processing.
- `processing`: Job is currently being indexed.
- `completed`: Job finished successfully.
- `failed`: Job encountered an error.
- `cancelled`: Job was cancelled by the user.

## Common Responses

### 202 Accepted (Standard for Ingest)
```json
{
  "status": "accepted",
  "message": "Document accepted for processing",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 400 Bad Request
Occurs if the payload is malformed or required fields are missing.
