# Agent Instructions — Retriva Chat Streaming

## Mission
Add **OpenAI-compatible streaming** support to `/v1/chat/completions`.

## Order of authority
1. `specs/005-chat-streaming/spec.md`
2. `specs/005-chat-streaming/openapi.yaml`
3. `.agent/rules/retriva-constitution.md`

## Non-negotiable rules
- Do not modify repository README.md
- Preserve non-streaming behavior
- Streaming must follow OpenAI SSE delta protocol
