# Agent Instructions for Retriva

## Mission
Build the first **Q&A-only** PoC for **Retriva**.

## Order of authority
1. `specs/001-qa-only-poc/spec.md`
2. `docs/mirror-contract.md`
3. `.agent/rules/retriva-constitution.md`
4. `specs/001-qa-only-poc/architecture.md`
5. `specs/001-qa-only-poc/tasks.md`
6. `docs/roadmap.md`

## Non-negotiable rules
- Do not expand scope beyond v0.1.1.
- Keep the corpus assumption fixed to a local static `wget` mirror.
- Use Python and OpenAI-compatible APIs.
- Keep answers grounded and cited.
- If evidence is insufficient, refuse gracefully.
- Preserve future seams for later phases.
