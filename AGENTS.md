# Agent Instructions — Retriva Markdown Injector

## Mission
Add a new **injector** for indexing local Markdown files into Retriva.

The injector must support recursive directory exploration from the CLI, similarly to the existing local ingestion flows.

## Order of authority
1. `specs/013-markdown-injector/spec.md`
2. `docs/markdown-injector-contract.md`
3. `.agent/rules/retriva-constitution.md`
4. `specs/013-markdown-injector/architecture.md`
5. `specs/013-markdown-injector/tasks.md`

## Non-negotiable rules
- Do not modify the repository root `README.md`
- Preserve existing injectors and ingestion modes
- Implement Markdown support as a **new injector**, not a rewrite of another injector
- Directory traversal must be recursive from a user-supplied root path
- Preserve Markdown structure where useful for chunking and citations (headings, lists, code fences, links)
- Keep CLI/API changes backward-compatible where possible
