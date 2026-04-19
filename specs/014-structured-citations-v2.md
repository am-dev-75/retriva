# SDD 014 — Structured Citations v2

## Purpose
Align Retriva citation output with OpenAI Responses API semantics and support per‑sentence inline citations for rich UI attribution in Open WebUI (without modifying Open WebUI).

## Key Additions
1. Responses‑style typed output (`output_text`, `citation`).
2. Segment‑level grounding via `citation_refs`.
3. Back‑compat envelope for Chat Completions using `tool_calls`.

## Acceptance
- Open WebUI renders Sources panel
- Works with ENABLE_RAG=false
- No Open WebUI fork required
