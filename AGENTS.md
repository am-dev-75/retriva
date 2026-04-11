# Agent Instructions — Retriva v0.2 Image Injection

## Mission

Add **image injection support** to Retriva, starting from the current HTML-only ingestion pipeline.

## Order of authority

1. `specs/002-image-injection/spec.md`
2. `.agent/rules/retriva-constitution.md`
3. `specs/002-image-injection/architecture.md`
4. `specs/002-image-injection/tasks.md`
5. `docs/roadmap.md`

## Non-negotiable rules

- Do not modify the repository main README.md
- Do not introduce OCR or VLM processing
- Keep image injection architecturally parallel to HTML injection
- Do not change retrieval logic
- Preserve backward compatibility with HTML-only injection
