# Feature Spec — 009 Core + Proprietary Extensions

## Goal

Introduce a pluggable architecture that decouples Retriva's key pipeline
stages from their implementations. The OSS core defines contracts (Python
`Protocol` classes) and ships default implementations. Proprietary or
enterprise packages can register alternative implementations at startup
without modifying, forking, or feature-flagging the core.

## Background

Today every pipeline stage is a hard-wired function call:

| Stage            | Current location                | Coupling |
|------------------|---------------------------------|----------|
| Retrieve chunks  | `qa/retriever.retrieve_top_chunks()` | direct call from `qa/answerer.py` |
| Chunk text       | `ingestion/chunker.create_chunks()` | direct call from ingestion routers |
| Parse HTML       | `ingestion/html_parser.extract_main_content()` | direct call from `ingest_HTML.py` |
| Describe images  | `ingestion/vlm_describer.describe_image()` | direct call from `image_parser.py` |
| Build prompt     | `qa/prompting.build_prompt()`   | direct call from `qa/answerer.py` |

An enterprise edition might need a hybrid (dense + sparse) retriever, an
LLM-based re-ranker, a PDF chunker, or a proprietary VLM — all without
touching the files above.

## In scope

- **Protocols** for the five stages listed above.
- **CapabilityRegistry** — a thread-safe singleton mapping capability names
  to prioritised implementations.
- **Default registrations** — the existing functions wrapped so they satisfy
  the protocols and are registered at priority 100.
- **Extension discovery** — at startup the core reads
  `RETRIVA_EXTENSIONS` (comma-separated dotted module paths) and calls each
  module's `register(registry)` function.
- **Core refactoring** — `answerer.py`, `ingest_HTML.py`, `ingest_image.py`,
  `ingest_text.py` resolve implementations via the registry instead of
  direct imports.
- **Regression tests** ensuring the system behaves identically with zero
  extensions loaded.

## Out of scope

- License enforcement, DRM, or entitlement checks.
- Authentication / RBAC.
- CI/CD, packaging, or wheel distribution of extensions.
- Multi-tenancy or per-request implementation switching.
- Changes to the repository root `README.md`.

## Constraints (from AGENTS.md)

- The OSS core **must not** import or depend on proprietary code.
- Proprietary code **may** depend on the OSS core.
- All extension points must be **explicit** and **documented**.
- No build-time or runtime forks of the OSS core.
