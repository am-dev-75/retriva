# Markdown Injector Contract

This document defines the expected input contract for indexing local Markdown files.

## 1. Input root
A user provides a root directory, recursively explored by the CLI.

Example shape:

```text
/root/markdown-corpus/
  handbook/
    architecture.md
    operations.markdown
  notes/
    bringup/
      startup-leds.md
  docs/
    power/
      methodology.md
```

## 2. Required input types
The root directory may contain:
- one or more `.md` or `.markdown` files in nested directories

## 3. Discovery rules
The injector must recursively walk the supplied root path and:
- collect candidate Markdown files
- ignore non-Markdown files unless future multi-source ingestion says otherwise

## 4. Extraction expectations
The injector should extract at minimum:
- derived document title when practical
- section headings / hierarchy when practical
- raw textual content
- local source path
- code-fence and list awareness if it improves chunking

## 5. Output metadata minimum
Every chunk/document emitted should retain enough metadata for citations/debugging:
- `doc_id`
- `source_path`
- `title` or derived document title
- `section_path` or heading path when available
- `chunk_id`
- `chunk_index`
- `language` when detectable

## 6. Failure handling
Unreadable or malformed Markdown should not crash ingestion. Files may be skipped or partially indexed with diagnostic logging.

## 7. CLI behavior
The CLI should support invoking this injector recursively from a directory root, similarly to the existing local mirror ingestion flow.
Backward-compatible CLI evolution is preferred.
