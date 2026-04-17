# Agent Instructions — Retriva PDF Injector

## Mission
Add a new **injector** for indexing local PDF files into Retriva.

The injector must support recursive directory exploration from the CLI, similarly to the existing local mirror ingestion flows.

## Order of authority
1. `specs/011-pdf-injector/spec.md`
2. `docs/pdf-injector-contract.md`
3. `.agent/rules/retriva-constitution.md`
4. `specs/011-pdf-injector/architecture.md`
5. `specs/011-pdf-injector/tasks.md`

## Non-negotiable rules
- Do not modify the repository root `README.md`
- Preserve existing injectors and ingestion modes
- Implement PDF support as a **new injector**, not a rewrite of another injector
- Directory traversal must be recursive from a user-supplied root path
- Prefer text extraction from embedded PDF text first; OCR is optional and must not be required for this increment
- Keep CLI/API changes backward-compatible where possible
