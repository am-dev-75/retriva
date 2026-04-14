# Implementation Plan — 009 Core + Proprietary Extensions

## Phase 1 — Protocols and Registry

1. Create `src/retriva/protocols.py` with `Retriever`, `Chunker`,
   `HTMLParser`, `VLMDescriber`, and `PromptBuilder` protocols.
2. Create `src/retriva/registry.py` with `CapabilityRegistry` singleton
   (thread-safe, priority-based selection, same pattern as `JobManager`).

## Phase 2 — Wrap existing code as default implementations

Each existing module keeps its current functions _and_ adds a class that
implements the matching protocol. The class is a thin adapter:

| Capability      | Module                        | Default class           |
|-----------------|-------------------------------|-------------------------|
| `retriever`     | `qa/retriever.py`             | `DefaultRetriever`      |
| `chunker`       | `ingestion/chunker.py`        | `DefaultChunker`        |
| `html_parser`   | `ingestion/html_parser.py`    | `DefaultHTMLParser`     |
| `vlm_describer` | `ingestion/vlm_describer.py`  | `DefaultVLMDescriber`   |
| `prompt_builder`| `qa/prompting.py`             | `DefaultPromptBuilder`  |

Each module calls `CapabilityRegistry().register(name, cls, priority=100)`
at import time.

## Phase 3 — Refactor call sites to use the registry

| Call site                          | Change                                     |
|------------------------------------|---------------------------------------------|
| `qa/answerer.py`                   | Use `registry.get_instance("retriever")`    |
| `qa/answerer.py`                   | Use `registry.get_instance("prompt_builder")`|
| `ingestion_api/routers/ingest_HTML.py` | Use `registry.get_instance("html_parser")` and `registry.get_instance("chunker")` |
| `ingestion_api/routers/ingest_image.py` | Use `registry.get_instance("vlm_describer")` |
| `ingestion_api/routers/ingest_text.py`  | Use `registry.get_instance("chunker")`      |
| `ingestion/image_parser.py`        | Use `registry.get_instance("vlm_describer")` |

## Phase 4 — Extension discovery

1. Add `RETRIVA_EXTENSIONS` to `config.py` as an optional
   `str` setting (default empty).
2. In both `openai_api/main.py` and `ingestion_api/main.py` lifespan hooks,
   call `CapabilityRegistry().load_extensions()` which:
   - Splits the env var on commas.
   - Imports each module.
   - Calls `module.register(registry)`.

## Phase 5 — Verification

1. **Unit tests** (`tests/test_registry.py`):
   - Register two implementations, higher-priority wins.
   - Thread-safety: concurrent registrations from multiple threads.
   - `get()` with no registrations raises `KeyError`.
2. **Integration test** (`tests/test_extension_loading.py`):
   - Create a tiny mock extension module in `tests/fixtures/`.
   - Set `RETRIVA_EXTENSIONS` env var pointing to it.
   - Verify the mock implementation is selected over the default.
3. **Regression**: all existing tests (bilingual, jobs, OpenAI, ingestion)
   pass without `RETRIVA_EXTENSIONS` set.
