# Agent Instructions — Retriva Open WebUI Integration (Refined)

## Mission
Expose Retriva as a **remote RAG backend** fully compatible with **Open WebUI**.

## Order of authority
1. `specs/004-open-webui-integration/spec.md`
2. `specs/004-open-webui-integration/openapi.yaml`
3. `.agent/rules/retriva-constitution.md`
4. `specs/004-open-webui-integration/architecture.md`
5. `specs/004-open-webui-integration/tasks.md`

## Non-negotiable rules
- Do not modify the repository main README.md
- Treat Open WebUI as an external client
- `/v1/chat/completions` MUST be OpenAI-compatible
- Support multiple knowledge bases (collections)
- Preserve existing ingestion and retrieval logic
