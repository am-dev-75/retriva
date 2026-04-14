"""Mock extension module for testing extension discovery."""


class MockRetriever:
    """A fake retriever that always returns a fixed result."""

    def retrieve(self, query: str, top_k: int):
        return [{"text": "mock result", "doc_id": "mock_doc", "page_title": "Mock"}]


def register(registry):
    """Called by CapabilityRegistry.load_extensions()."""
    registry.register("retriever", MockRetriever, priority=200)
