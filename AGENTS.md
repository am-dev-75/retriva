# Agent Instructions — Retriva MediaWiki Export Injector

## Mission
Add a new **injector** for indexing a **local MediaWiki native export mirror** consisting of:
- one or more `*.xml` MediaWiki export files
- an `assets/` directory containing exported images/files

The new injector must be invokable recursively from the CLI, similarly to the existing local mirror ingestion flow.

## Order of authority
1. `specs/010-mediawiki-export-injector/spec.md`
2. `docs/mediawiki-export-contract.md`
3. `.agent/rules/retriva-constitution.md`
4. `specs/010-mediawiki-export-injector/architecture.md`
5. `specs/010-mediawiki-export-injector/tasks.md`

## Non-negotiable rules
- Do not modify the repository root `README.md`
- Preserve existing wget-mirror ingestion behavior
- Implement this as a **new injector**, not a rewrite of the HTML injector
- Directory traversal must be recursive from a user-supplied root path
- The injector must support MediaWiki XML export + local assets/images
- Keep API/CLI changes backward-compatible where possible
