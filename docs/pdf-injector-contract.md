# PDF Injector Contract

This document defines the expected input contract for indexing local PDF files.

## 1. Input root
A user provides a root directory, recursively explored by the CLI.

Example shape:

```text
/root/pdf-corpus/
  manuals/
    board_x_manual.pdf
  diagnostics/
    startup_leds.pdf
  archived/
    2021/
      fan_curve_notes.pdf
```

## 2. Required input types
The root directory may contain:
- one or more `.pdf` files in nested directories

## 3. Discovery rules
The injector must recursively walk the supplied root path and:
- collect candidate PDF files
- ignore non-PDF files unless future multi-source ingestion says otherwise

## 4. Extraction expectations
The injector should extract at minimum:
- document title when derivable
- page-by-page embedded text
- page numbers
- local source path

## 5. Output metadata minimum
Every chunk/document emitted should retain enough metadata for citations/debugging:
- `doc_id`
- `source_path`
- `page_title` or derived document title
- `page_number` or page range
- `chunk_id`
- `chunk_index`
- `language` when detectable

## 6. Failure handling
Unreadable, encrypted, or image-only PDFs should not crash ingestion. They may be skipped or partially indexed with diagnostic logging.

## 7. CLI behavior
The CLI should support invoking this injector recursively from a directory root, similarly to the existing local mirror ingestion flow.
Backward-compatible CLI evolution is preferred.
