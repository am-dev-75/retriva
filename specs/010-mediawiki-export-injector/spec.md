# Feature Spec — 010 MediaWiki Native Export Injector

## Goal

Add a new injector that indexes a **local MediaWiki native export mirror**
consisting of one or more `*.xml` export files and an optional `assets/`
subtree containing images/files. The injector is a peer of the existing
HTML injector — it does not replace or modify it.

## Background

Retriva already supports local static HTML mirrors (`wget`-style).  Some
wikis are exported using MediaWiki's native `Special:Export` or
`dumpBackup.php`, producing XML files rather than HTML pages.  A second
ingestion mode is needed so these exports can be indexed without first
converting them to HTML.

### Input shape (from `docs/mediawiki-export-contract.md`)

```
/root/export-mirror/
  wiki_backup_20260402.xml      ← MediaWiki XML export
  assets/
    images/
      0/ 1/ … a/ b/ archive/
      dave.jpg  dave.png
```

### MediaWiki XML structure (simplified)

```xml
<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">
  <siteinfo>
    <sitename>Example Wiki</sitename>
    <namespaces>
      <namespace key="0">Main</namespace>
      <namespace key="6">File</namespace>
    </namespaces>
  </siteinfo>
  <page>
    <title>Infrastructure/Database</title>
    <ns>0</ns>
    <id>42</id>
    <revision>
      <timestamp>2026-03-15T10:22:00Z</timestamp>
      <text xml:space="preserve">
        == Overview ==
        The database runs PostgreSQL 15…
        [[File:db_schema.png|thumb|Schema diagram]]
      </text>
    </revision>
  </page>
</mediawiki>
```

## In scope

- Recursive directory discovery for `*.xml` MediaWiki export files
- XML parsing: `<page>`, `<title>`, `<ns>`, `<revision>/<text>`
- Wikitext-to-plain-text conversion (strip markup, tables, templates)
- `[[File:…]]` / `[[Image:…]]` reference extraction
- Best-effort resolution of file references against `assets/` subtree
- VLM enrichment of resolved images (via registry, same as HTML injector)
- Emission of `ParsedDocument` / `Chunk` objects compatible with the
  existing indexing pipeline
- New ingestion API endpoint (`/api/v1/ingest/mediawiki`)
- CLI integration via `--injector mediawiki_export` flag
- Metadata sufficient for citations: `page_title`, `source_xml_path`,
  `namespace`, `language`, `linked_assets`

## Out of scope

- Live MediaWiki API integration or synchronization
- Replacing the HTML injector
- UI changes
- OCR as a requirement
- Large-scale deduplication across multiple export backups
- Translation pipelines

## Functional requirements

### FR1 — Recursive discovery
The system shall recursively explore the supplied root directory, detect
candidate `*.xml` MediaWiki export files (validated by root element
sniffing for `<mediawiki`), and catalog local assets under `assets/`.

### FR2 — New injector implementation
The system shall implement the export support as a dedicated injector
(`mediawiki_export_parser.py`) rather than modifying the HTML injector.

### FR3 — XML page parsing
The system shall parse `<page>` elements using `xml.etree.ElementTree`
with iterparse (streaming) for memory efficiency.  For each page it
extracts: `<title>`, `<ns>`, `<id>`, latest `<revision>/<text>`.

### FR4 — Wikitext processing
The system shall convert raw wikitext to plain text suitable for
chunking by:
- Stripping MediaWiki markup (`'''bold'''`, `''italic''`, `== headings ==`)
- Expanding simple wikilinks (`[[Target|Label]]` → `Label`)
- Removing templates (`{{…}}`) and HTML tags
- Preserving paragraph structure

### FR5 — Asset linkage
The system shall extract `[[File:name.ext]]` / `[[Image:name.ext]]`
references and attempt to resolve them against the local `assets/`
subtree using case-insensitive filename matching.

### FR6 — CLI support
The CLI `ingest` and `reindex` commands shall accept an optional
`--injector mediawiki_export` flag. When set, the CLI uses the new
discovery and handler logic instead of the default HTML/image/text
pipeline. The default behavior (no flag) is unchanged.

### FR7 — Citation/debug metadata
Every emitted chunk shall carry:
- `doc_id` — `{xml_filename}#{page_id}`
- `source_path` — path to the source XML file
- `page_title` — from `<title>`
- `language` — detected from `<siteinfo>` or `xml:lang`, default `"en"`
- `chunk_type` — `"text"` or `"image"`

## Acceptance summary

The feature is accepted when a user can run:
```
python -m retriva.cli ingest --path /data/wiki-export --injector mediawiki_export
```
and have XML pages parsed, plain text chunked, local images resolved and
VLM-enriched, and all content indexed — without breaking existing
`wget`-mirror ingestion.
