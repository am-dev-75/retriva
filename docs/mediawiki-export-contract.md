# MediaWiki Export Mirror Contract

This document defines the expected input contract for indexing a local MediaWiki native export mirror.

## 1. Input root
A user provides a root directory, recursively explored by the CLI.

Example shape:

```text
/root/export-mirror/
  wiki_backup_20260402.xml
  assets/
    images/
      0/
      1/
      ...
      a/
      b/
      archive/
      dave.jpg
      dave.png
```

## 2. Required input types
The root directory may contain:
- one or more `*.xml` MediaWiki export files
- one `assets/` subtree containing image/file exports

## 3. Discovery rules
The injector must recursively walk the supplied root path and:
- collect candidate XML export files
- collect local asset/image files under `assets/`
- avoid treating binary assets as standalone text documents

## 4. XML parsing expectations
The injector should parse from the MediaWiki XML export at minimum:
- page title
- namespace when available
- revision text/content
- internal file/image references when available
- timestamps and contributor metadata if useful

## 5. Asset resolution expectations
When a page references a file/image, the injector should attempt to resolve it against the local `assets/` subtree.
When resolution is not possible, the page should still be indexed with unresolved file reference metadata when available.

## 6. Output metadata minimum
Every chunk/document emitted should retain enough metadata for citations/debugging:
- `doc_id`
- `page_title`
- `source_xml_path`
- `chunk_id`
- `chunk_index`
- `language` when detectable
- `linked_assets` / file references when available

## 7. CLI behavior
The CLI should support invoking this injector recursively from a directory root, similarly to the existing local mirror ingestion flow.
Backward-compatible CLI evolution is preferred.
