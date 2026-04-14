# Architecture — 009 Core + Proprietary Extensions

## Layered view

```
┌─────────────────────────────────────────────┐
│  FastAPI apps (openai_api, ingestion_api)    │
│  ── resolve implementations via Registry ── │
├─────────────────────────────────────────────┤
│  CapabilityRegistry  (src/retriva/registry.py)│
│  ── maps capability name → impl + priority ─│
├─────────────────────────────────────────────┤
│  Protocols           (src/retriva/protocols.py)│
│  ── Retriever, Chunker, HTMLParser,         │
│     VLMDescriber, PromptBuilder             │
├─────────────────────────────────────────────┤
│  Default OSS implementations                │
│  ── existing modules, wrapped as classes ── │
├═════════════════════════════════════════════┤
│  Extension packages (optional, external)    │
│  ── loaded via RETRIVA_EXTENSIONS env var ──│
└─────────────────────────────────────────────┘
```

## Protocols (`src/retriva/protocols.py`)

Each protocol defines the minimal interface a capability must satisfy.

```python
from typing import Protocol, List, Dict
from pathlib import Path
from retriva.domain.models import ParsedDocument, Chunk

class Retriever(Protocol):
    def retrieve(self, query: str, top_k: int) -> List[Dict]: ...

class Chunker(Protocol):
    def create_chunks(self, document: ParsedDocument) -> List[Chunk]: ...

class HTMLParser(Protocol):
    def extract_content(self, html: str) -> str | None: ...
    def extract_language(self, html: str) -> str: ...

class VLMDescriber(Protocol):
    def describe(self, image_path: Path) -> str: ...

class PromptBuilder(Protocol):
    def build_prompt(self, question: str, chunks: List[Dict]) -> str: ...
```

## CapabilityRegistry (`src/retriva/registry.py`)

Thread-safe singleton mapping capability names to implementations.

```python
class CapabilityRegistry:
    def register(self, name: str, impl_class: type, priority: int = 100): ...
    def get(self, name: str) -> type: ...   # returns highest-priority class
    def get_instance(self, name: str): ...  # returns instantiated singleton
```

- **Priority model**: default OSS = 100; extensions use higher values
  (e.g. 200). Highest priority wins.
- **Thread safety**: all mutations guarded by `threading.Lock`.
- **Singleton**: `CapabilityRegistry()` always returns the same instance
  (double-checked locking, same pattern as `JobManager`).

## Extension discovery

At application startup (in the FastAPI `lifespan` hooks of both
`openai_api/main.py` and `ingestion_api/main.py`):

1. Read `RETRIVA_EXTENSIONS` environment variable.
2. For each comma-separated module path, `importlib.import_module(path)`.
3. Call `module.register(registry)` — extensions use this hook to register
   their higher-priority implementations.
4. If `RETRIVA_EXTENSIONS` is unset or empty, the system runs with defaults
   only (zero-extension mode).

## How core code changes

### Before (direct coupling)

```python
# qa/answerer.py
from retriva.qa.retriever import retrieve_top_chunks
chunks = retrieve_top_chunks(question, retriever_top_k=k)
```

### After (registry-based)

```python
# qa/answerer.py
from retriva.registry import CapabilityRegistry
registry = CapabilityRegistry()
retriever = registry.get_instance("retriever")
chunks = retriever.retrieve(question, top_k=k)
```

The direct imports of concrete implementations are removed from the call
sites. The concrete modules still exist and register themselves as defaults.

## Dependency rule

```
OSS core  →  protocols, registry, default impls  (no extension imports)
Extensions →  may import from retriva.*
```

This is enforced structurally: the core never references any module path
outside `src/retriva/`.
