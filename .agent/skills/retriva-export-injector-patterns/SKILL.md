---
name: retriva-export-injector-patterns
description: Guidance for building a MediaWiki native export injector for Retriva.
---

# Retriva MediaWiki Export Injector Patterns

## Core input shape
The export mirror should be treated as a recursive directory containing:
- one or more MediaWiki export XML files, e.g. `wiki_backup_20260402.xml`
- an `assets/` subtree with files/images, typically under `assets/images/`

## Preferred processing flow
1. recursively scan the root directory
2. detect candidate XML export files
3. parse MediaWiki pages, revisions, text bodies, and file references from XML
4. resolve linked file/image references against the local `assets/` subtree when possible
5. emit document/chunk objects compatible with the existing indexing pipeline
6. preserve source metadata sufficient for citations and debugging

## Guardrails
- Do not assume HTML pages exist
- Do not assume `wget` rewritten links exist
- Keep recursive discovery deterministic and conservative
